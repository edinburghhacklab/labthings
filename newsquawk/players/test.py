import logging

from .base import BasePlayer, BaseTask

logger = logging.getLogger(__name__)

class TestTask(BaseTask):
    def __init__(self, payload, *args, **kwargs):
        self.payload = payload
        self.args = args
        self.kwargs = kwargs
    def prepare(self):
        pass
    def is_ready(self):
        return True
    def play(self):
        logging.info('TestPlayer Task.play() -> payload={!r} args={} kwargs{}'.format(self.payload, self.args, self.kwargs))
    def abort(self):
        pass

class TestPlayer(BasePlayer):
    def __init__(self):
        logger.debug('TestPlayer() init')
    def task(self, payload, *args, **kwargs):
        logger.debug('TestPlayer.task(payload={!r}, args={}, kwargs={})'.format(payload, args, kwargs))
        task = TestTask(payload, *args, **kwargs)
        return task
