import logging
import os
import random
import subprocess

from .base import BasePlayer, BaseTask

class FilesTask(BaseTask):
    def __init__(self, raw_filenames, sounds_path, max_play_time):
        self.sounds_path = sounds_path
        self.requested_filenames = raw_filenames.split(',')
        self.selected_filenames = [self._findfile(os.path.join(self.sounds_path, filename)) for filename in self.requested_filenames]
        self.selected_filenames = [x for x in self.selected_filenames if x is not None]
        self.max_play_time = max_play_time * len(self.selected_filenames)
        self.player = None
        self.command = None
        # Can only play a list of files if they all have the same extension
        selected_exts = set([os.path.splitext(filename)[1] for filename in self.selected_filenames])
        if len(self.selected_filenames) > 0 and len(selected_exts) == 1:
            ext = selected_exts.pop()
            if ext == '.mp3':
                self.player = 'mpg123'
                self.command = ['mpg123', '-q', '-m'] + self.selected_filenames
            else:
                self.player = 'play'
                self.command = ['play', '-q'] + self.selected_filenames

    def __str__(self):
        return "<Files {!r} -> {!r} [{}]>".format(','.join(self.requested_filenames), ','.join([os.path.relpath(filename, self.sounds_path) for filename in self.selected_filenames]), self.player)

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

class FilesPlayer(BasePlayer):
    def __init__(self, sounds_path, max_play_time=15):
        self.sounds_path = sounds_path
        self.max_play_time = max_play_time
    def task(self, filename):
        task = FilesTask(filename, sounds_path=self.sounds_path, max_play_time=self.max_play_time)
        return task
