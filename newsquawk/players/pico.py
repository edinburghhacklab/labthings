import subprocess

from .base import BasePlayer

class PicoPlayer(BasePlayer):
    def __init__(self, text, max_play_time=15):
        self.text = text
        self.max_play_time = max_play_time
    def play(self):
        subprocess.call(['timeout', str(self.max_play_time), '/home/pi/pico.sh', self.text])
