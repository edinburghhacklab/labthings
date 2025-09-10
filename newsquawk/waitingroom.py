import subprocess

class WaitingRoom:
    def __init__(self, filename):
        command = ['mpg123', '-q', '-m', filename]
        self.process = subprocess.Popen(command)
    def stop(self):
        if self.process:
            if self.process.poll() is None:
                self.process.kill()
                self.process.wait()