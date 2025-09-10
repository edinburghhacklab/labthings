import hashlib
import os
import subprocess
import logging

import boto3

from .base import BasePlayer, BaseTask

CHIME_FILENAME = "/home/pi/sounds/scotrail/non-vocal/[4_rising_chimes].mp3"

class PollyTask(BaseTask):
    def __init__(self, text, voice, cache_dir, max_play_time=15, do_chime=False):
        self.text = text
        self.voice = voice
        self.cache_dir = cache_dir
        self.max_play_time = max_play_time
        self.do_chime = do_chime
        self.voice = voice[0].upper() + voice[1:]
        self.hash = hashlib.sha1(text.encode()).hexdigest()
        self.filename = "{}/{}-{}.mp3".format(self.cache_dir, self.voice, self.hash)
        self.polly = boto3.client('polly')

    def __str__(self):
        return "<Polly voice={!r} text={!r} do_chime={}>".format(self.voice, self.text, self.do_chime)

    def prepare(self):
        pass

    def is_ready(self):
        return True

    def play(self):
        if os.path.exists(self.filename):
            logging.debug("polly: filename {} found".format(self.filename))
        else:
            logging.debug("polly: filename {} not found - requesting".format(self.filename))
            if self.text.startswith('<speak>'):
                logging.debug('polly: using SSML')
                text_type = 'ssml'
            else:
                text_type = 'text'
            response = self.polly.synthesize_speech(
                OutputFormat='mp3',
                Text=self.text,
                TextType=text_type,
                VoiceId=self.voice
            )
            with open(self.filename, 'wb') as fh:
                fh.write(response['AudioStream'].read())
        if self.do_chime:
            logging.debug("play() calling playback command for chime")
            self.playback = subprocess.Popen(
                ['mpg123', '-q', '-m', CHIME_FILENAME]
            )
            try:
                result = self.playback.wait(timeout=self.max_play_time)
                logging.debug("play() command returned {}".format(result))
            except subprocess.TimeoutExpired:
                logging.debug("play() timed out")
                try:
                    self.playback.kill()
                    self.playback.wait()
                except AttributeError:
                    pass
        logging.debug("play() calling playback command")
        self.playback = subprocess.Popen(
            ['mpg123', '-q', '-m', self.filename]
        )
        try:
            result = self.playback.wait(timeout=self.max_play_time)
            logging.debug("play() command returned {}".format(result))
        except subprocess.TimeoutExpired:
            logging.debug("play() timed out")
            try:
                self.playback.kill()
                self.playback.wait()
            except AttributeError:
                pass
        self.playback = None

    def abort(self):
        try:
            self.playback.kill()
        except AttributeError:
            pass

class PollyPlayer(BasePlayer):
    def __init__(self, cache_dir, default_voice, max_play_time=15):
        self.cache_dir = cache_dir
        self.default_voice = default_voice
        self.max_play_time = max_play_time
    def task(self, text, voice=None, do_chime=False):
        if voice is None:
            voice = self.default_voice
        return PollyTask(text, voice, self.cache_dir, max_play_time=self.max_play_time, do_chime=do_chime)
