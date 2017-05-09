#!/usr/bin/python
# -*- coding: utf-8 -*-
# author: toka
import os
import threading
import subprocess
import sys
import shutil
import time
import signal

class worker(threading.Thread):

	def __init__(self, task, argv, callback):
		super(worker, self).__init__()
		self.__cb = callback
		self.__task = task
		self.__argv = argv
	def run(self):
		ret = None
		try:
			ret = self.__task(*self.__argv)
		except Exception, e:
			print e.message
		self.__cb(ret)


class mqThread:
	
	outputLock = threading.Lock()

	def __init__(self, num, limit, execute):
		self.__num = num
		self.__limit = limit
		self.__excu = execute
		self.__cnt = 0
		self.__lock = threading.Lock()
		self.__silent = False

	def __cb(self, index):
		self.__lock.acquire()
		self.__cnt -= 1
		endTime = time.time()
		self.__lock.release()
		if not self.__silent:
			self.outputLock.acquire()
			print 'Task[%06d]: ended. START: %d, END: %d, RUNTIME: %d' % (index, self.__beginTime[index], endTime, endTime - self.__beginTime[index])
			self.outputLock.release()
	
	def __pre_execute(self, index):
		self.__excu(index)
		return index + 1

	def __quit(self, signum, frame):
		self.outputLock.acquire()
		print 'All tasks stoped. SIGNUM: [%03d]' % (signum)
		self.outputLock.release()
		sys.exit()
	
	def start(self, silent = False):
		signal.signal(signal.SIGINT, self.__quit)
		signal.signal(signal.SIGTERM, self.__quit)
		s = threading.Semaphore(self.__limit)
		i = 0
		self.__cnt = 0
		self.__silent = silent
		self.__beginTime = {}
		while i < self.__num:
			if self.__cnt < self.__limit:
				self.__lock.acquire()
				self.__cnt += 1
				i += 1
				self.__beginTime[i] = time.time()
				if not silent:
					self.outputLock.acquire()
					print 'Task [%06d]: start...' % (i)
					self.outputLock.release()
				self.__lock.release()
				t = worker(task = self.__pre_execute, argv = tuple([i - 1]), callback = self.__cb)
				t.setDaemon(True)
				t.start()
		main_t = threading.currentThread()
		for t in threading.enumerate():
			if t is main_t:
				continue
			t.join()

def generate(taskid):
	for i in range(5+taskid*2):
		for j in range(1000000):
			pass
		mqThread.outputLock.acquire()
		print '%d running...' % (taskid+1)
		mqThread.outputLock.release()
		time.sleep(0.2)
if __name__=='__main__':
	mq = mqThread(20,12,generate)
	mq.start()



