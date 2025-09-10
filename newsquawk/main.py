#!/usr/bin/env python3

import json
import logging
import re
import queue
import subprocess
import threading
import os
import time

import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.INFO)
logging.getLogger('boto3').setLevel(logging.CRITICAL)

try:
    import RPi.GPIO as GPIO
    RPI_GPIO = True
except ImportError:
    logging.exception('Continuing without RPI.GPIO')
    RPI_GPIO = False

#from players.base import BasePlayer
#from players.pico import PicoPlayer
from players.file import FilePlayer
from players.files import FilesPlayer
from players.polly import PollyPlayer
#from waitingroom import WaitingRoom
from players.test import TestPlayer

TOPIC_RE = re.compile(r'sound/([a-z0-9\-]+)/(.+)')
MAX_PLAY_TIME = 15
MAX_TIME_OUT = 600
SOUNDS_PATH = '/home/pi/sounds'
DEFAULT_VOLUME = 90

TEST_PLAYER = TestPlayer()
POLLY_PLAYER = PollyPlayer(default_voice='Brian', cache_dir=os.path.join(SOUNDS_PATH, 'amazon'), max_play_time=MAX_PLAY_TIME)
FILE_PLAYER = FilePlayer(sounds_path=SOUNDS_PATH, max_play_time=MAX_PLAY_TIME + 5)
FILES_PLAYER = FilesPlayer(sounds_path=SOUNDS_PATH, max_play_time=MAX_PLAY_TIME)
MQTT_SESSION = mqtt.Client()

def irc_send(message, prefix='squawk: '):
    MQTT_SESSION.publish('irc/send', json.dumps({'to': '#edinhacklab-things',  'message': prefix + message}))

def parse_topic(topic):
    args = []
    kwargs = {}
    for word in topic.split('/'):
        try:
            k, v = word.split('=', 1)
            kwargs[k] = v
        except ValueError:
            args.append(word)
    return args, kwargs

class SpeakerManager:
    def __init__(self):
        self.channels = {
            'g1': 3,
            'g2': 5,
            'g8': 8,
            'g11': 7,
        }
        self.all_channels = [value for value in self.channels.values()]
        if RPI_GPIO:
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(self.all_channels, GPIO.OUT)
            GPIO.output(self.all_channels, 1)
    def set_rooms(self, rooms=[]):
        if RPI_GPIO:
            if 'all' in rooms:
                logging.debug('setting rooms=all')
                GPIO.output(self.all_channels, 1)
            else:
                logging.debug('setting rooms={}'.format(rooms))
                for room, channel in self.channels.items():
                    if room in rooms:
                        GPIO.output(channel, 1)
                    else:
                        GPIO.output(channel, 0)
    def set_volume(self, level):
        if type(level) is int:
            if level >= 0 or level <= 100:
                subprocess.call(['/usr/bin/amixer', '-M', 'sset', 'PCM', '{}%'.format(level)])

class SoundQueue(threading.Thread):
    def __init__(self):
        super(SoundQueue, self).__init__()
        self.queue = queue.Queue()
        self.current_task = None
        self.daemon = True
        self.silent_until = 0
        self.start()
        
    def add(self, rooms, volume, task):
        if time.time() >= self.silent_until:
            logging.debug("adding to queue: rooms={} task={}".format(rooms, task))
            task.prepare()
            self.queue.put((rooms, volume, task))
        else:
            logging.debug("in time-out, not adding to queue")

    def kill(self):
        logging.debug("emptying queue")
        irc_send("kill command received")
        try:
            while True:
                self.queue.get(block=False)
        except queue.Empty:
            pass
        if self.current_task:
            try:
                logging.debug("stopping current task {}".format(self.current_task))
                self.current_task.abort()
            except AttributeError:
                logging.debug("current task doesn't handle .abort()")
        else:
            logging.debug("no current task to abort")

    def time_out(self, seconds):
        logging.debug("setting time-out for {} seconds".format(seconds))
        self.silent_until = max(self.silent_until, time.time() + seconds)
        irc_send('in time-out for the next {:.0f} seconds'.format(self.silent_until - time.time()))
        self.kill()

    def run2(self):
        while True:
            logging.debug("in SoundQueue.run() waiting for queue")
            job = self.queue.get(block=True)
            if job is not None:
                rooms, volume, task = job
                logging.debug("dequeueing rooms={} task={}".format(rooms, task))
                while not task.is_ready():
                    logging.debug("waiting for task to become ready")
                    time.sleep(0.5)
                speakers.set_rooms(rooms)
                speakers.set_volume(volume)
                self.current_task = task
                irc_send('playing rooms={} volume={}% task={}'.format('-'.join(rooms), volume, task))
                try:
                    self.current_task.play()
                except Exception as e:
                    logging.exception('Exception in {} .play()'.format(self.current_task))
                self.current_task = None

    def run(self):
        while True:
            try:
                self.run2()
            except:
                logging.exception('Exception in SoundQueue thread')
            time.sleep(0.5)
                
def on_connect(client, userdata, flags, rc):
    client.subscribe('sound/#')

def on_message(client, userdata, msg):
    # ignore retained (non-realtime) messages
    if msg.retain:
        return

    logging.debug("* {} {}".format(msg.topic, msg.payload))

    payload = msg.payload.decode()

    if msg.topic == 'sound/kill':
        sq.kill()
        return

    if msg.topic == 'sound/time-out':
        try:
            t = int(payload)
            t = min(t, MAX_TIME_OUT)
        except ValueError:
            return
        sq.time_out(t)
        return
        
    m = TOPIC_RE.match(msg.topic)
    if m:
        rooms = m.group(1).lower().split('-')
        args, kwargs = parse_topic(m.group(2))
        command = args.pop(0)
        
        try:
            volume = int(kwargs.pop('vol', DEFAULT_VOLUME))
        except ValueError:
            volume = DEFAULT_VOLUME

        logging.debug("rooms={} volume={} command={} args={} kwargs={}".format(rooms, volume, command, args, kwargs))

        if command == 'test':
            sq.add(
                rooms,
                volume,
                TEST_PLAYER.task(payload, *args, **kwargs)
            )

        # announce has an extra chime
        if command == 'speak' or command == 'announce':
            sq.add(
                rooms,
                volume,
                POLLY_PLAYER.task(payload, do_chime=(command == 'announce'))
            )

        if command == 'polly':
            voice = args.pop(0)
            sq.add(
                rooms,
                volume,
                POLLY_PLAYER.task(payload, voice=voice)
            )

        if command == 'play':
            sq.add(
                rooms,
                volume,
                FILE_PLAYER.task(payload)
            )

        if command == 'playlist':
            sq.add(
                rooms,
                volume,
                FILES_PLAYER.task(payload)
            )

        #if command == 'pico':
        #    mod = PicoPlayer(text=payload)
        #    sq.add(rooms.split('-'), mod)
        #    return

sq = SoundQueue()
speakers = SpeakerManager()

m = MQTT_SESSION
m.on_connect = on_connect
m.on_message = on_message
m.connect("mqtt.hacklab")

irc_send('ready')

m.loop_forever()
