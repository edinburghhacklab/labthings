import logging
import os
import random
import subprocess

from .base import BasePlayer, BaseTask

class FileTask(BaseTask):
    def __init__(self, filename, sounds_path, max_play_time):
        self.sounds_path = sounds_path
        self.max_play_time = max_play_time
        self.requested_filename = filename
        self.selected_filename = self._findfile(os.path.join(self.sounds_path, filename))
        self.player = None
        self.command = None
        if self.selected_filename:
            if self.selected_filename == '/home/pi/sounds/countdown.mp3':
                self.max_play_time = 32
            if self.selected_filename == '/home/pi/sounds/mii.mp3':
                self.max_play_time = 35
            base, ext = os.path.splitext(self.selected_filename)
            if ext == '.mp3':
                self.player = 'mpg123'
                self.command = ['mpg123', '-q', '-m', self.selected_filename]
            else:
                self.player = 'play'
                self.command = ['play', '-q', self.selected_filename]

    def __str__(self):
        return "<File {!r} -> {!r} [{}]>".format(self.requested_filename, os.path.relpath(self.selected_filename, self.sounds_path), self.player)

    def _allfiles(self, path, exts=[".mp3", ".wav"]):
        allfiles = []
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                base, ext = os.path.splitext(filename)
                if ext in exts:
                    allfiles.append(os.path.join(dirpath, filename))
        return allfiles

    def _findfile(self, filename):
        if filename.endswith('/'):
            # pick a random file from a directory
            candidates = []
            for f in self._allfiles(self.sounds_path):
                if f.startswith(filename):
                    candidates.append(f)
            if len(candidates) == 0:
                logging.error('No files matching %s' % (filename))
                return
            return random.choice(candidates)
        else:
            # single file requested
            filename2 = os.path.abspath(os.path.normpath(filename))
            if filename2.startswith(self.sounds_path + '/'):
                if os.path.isfile(filename2):
                    return filename
                else:
                    logging.error('File %s not found' % (filename))
                    return
            else:
                logging.error('File %s not under correct path' % (filename))
                return

    def play(self):
        if self.command:
            self.playback = subprocess.Popen(self.command)
            try:
                self.playback.wait(timeout=self.max_play_time)
            except subprocess.TimeoutExpired:
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

class FilePlayer(BasePlayer):
    def __init__(self, sounds_path, max_play_time=15):
        self.sounds_path = sounds_path
        self.max_play_time = max_play_time
    def task(self, filename):
        task = FileTask(filename, sounds_path=self.sounds_path, max_play_time=self.max_play_time)
        return task
