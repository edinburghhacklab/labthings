class BasePlayer:
    def task(self):
        raise NotImplemented

class BaseTask:
    def prepare(self):
        pass
    def is_ready(self):
        return True
    def play(self):
        pass
    def abort(self):
        pass
