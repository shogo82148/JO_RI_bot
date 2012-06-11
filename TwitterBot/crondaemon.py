#!/usr/bin/env python
# -*- coding:utf-8 -*-

from threading import Thread, Lock, Event
import datetime
import time
from croniter import croniter
import logging

logger = logging.getLogger("Bot.cron")

class CronItem(object):
    def __init__(self, cron_time, it, func, args=(), kargs={}, cron_id=None):
        self.cron_time = cron_time
        self.it = it
        self.func = func
        self.args = args
        self.kargs = kargs
        self.cron_id = cron_id

def total_seconds(td):
    if hasattr(td, 'total_seconds'):
        return td.total_seconds()
    else:
        return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10.0**6

class crondaemon(object):
    def __init__(self):
        self.running = True
        self._crons = []
        self._lock = Lock()
        self._event = Event()
        self._cron_id = 0
        
    def append(self, crontime, func, args=(), kargs={}, name=None):
        next_time = None
        it = None
        if isinstance(crontime, (unicode, str)):
            it = croniter(crontime)
            next_time = it.get_next(ret_type=datetime.datetime)
        elif isinstance(crontime, croniter):
            it = crontime
            next_time = it.get_next(ret_type=datetime.datetime)
        elif isinstance(crontime, datetime.datetime):
            next_time = crontime

        with self._lock:
            cron_id = name or ('cron-' + str(self._cron_id))
            self._cron_id += 1
            self._crons.append(CronItem(
                    cron_time = next_time,
                    it = it,
                    func = func,
                    args = args,
                    kargs = kargs,
                    cron_id = cron_id))
        self._event.set()
        return cron_id

    def delete(self, name):
        with self._lock:
            self._crons = [cron for cron in self._crons if cron.cron_id!=name]
        self._event.set()
        return name

    def hascron(self, name):
        for cron in self._crons:
            if cron.cron_id==name:
                return True
        return False

    def _run(self):
        logger.debug('Cron running...')
        while self.running:
            logger.debug('Cron load task')
            self._event.clear()
            with self._lock:
                cron = None
                if len(self._crons)>0:
                    cron = min(self._crons, key=lambda x: x.cron_time)
            
            if cron:
                delta = total_seconds(cron.cron_time - datetime.datetime.now())
                if delta>0:
                    logger.debug('Cron: waiting %ds for %s', delta, cron.cron_id)
                    self._event.wait(delta)
            else:
                logger.debug('Cron: there is no task. waiting for new task')
                self._event.wait()

            if self._event.is_set():
                logger.debug('Cron: Task list updated. Reload.')
                continue

            logger.debug('Cron: Execute task %s', cron.cron_id)
            if cron.it:
                cron.cron_time = cron.it.get_next(ret_type=datetime.datetime)
            else:
                self.delete(cron.cron_id)
            cron.func(*cron.args, **cron.kargs)

    def start(self, async=False):
        self._event.clear()
        self.running = True
        if async:
            Thread(target=self._run).start()
        else:
            self._run()

    def stop(self):
        self._event.set()
        self.running = False

def main():
    def func(cron, name):
        print [c.cron_id for c in cron._crons]
        print name, datetime.datetime.now()
        
    cron = crondaemon()
    print cron.append(datetime.datetime.now()+datetime.timedelta(seconds=10), func, (cron, "10 seconds delay",))
    print cron.append('* * * * *', func, (cron, "per minuite",))
    print cron.append('*/5 * * * *', func, (cron, "per five minutes",))
    print cron.append('0-30 * * * *', func, (cron, "0-30 minutes",))
    print cron.hascron('cron-2')
    print cron.hascron('cron-100')
    cron.start()
    time.sleep(60*60)
    
if __name__=='__main__':
    main()
