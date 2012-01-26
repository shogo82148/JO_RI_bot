#!/usr/bin/env python
# -*- coding:utf-8 -*-

from threading import Thread, Lock, Event
import datetime
import time
from croniter import croniter

class crondaemon:
    def __init__(self):
        self.running = True
        self._crons = []
        self._lock = Lock()
        self._event = Event()
        
    def append(self, crontime, func, args=(), kargs={}):
        it = croniter(crontime)
        with self._lock:
            self._crons.append([it.get_next(), it, func, args, kargs])
        self._event.set()

    def _run(self):
        while self.running:
            self._event.clear()
            with self._lock:
                cron = None
                if len(self._crons)>0:
                    cron = min(self._crons, key=lambda x: x[0])
            
            if cron:
                delta = cron[0] - time.time()
                if delta>0:
                    self._event.wait(delta)
            else:
                self._event.wait()

            if self._event.is_set():
                continue

            cron[0] = cron[1].get_next()
            cron[2](*cron[3], **cron[4])

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
    def func(name):
        print name, datetime.datetime.now()
        
    cron = crondaemon()
    cron.add('* * * * *', func, ("per minuite",))
    cron.add('*/5 * * * *', func, ("per five minutes",))
    cron.add('0-30 * * * *', func, ("0-30 minutes",))
    cron.start()
    time.sleep(60*60)
    
if __name__=='__main__':
    main()
