import httplib
import ftplib
from re import *
from copy import copy
import tempfile
import os
import cv2
from PyQt4.QtGui import *
from PyQt4 import QtCore
import sys
from math import *
from qimage2ndarray import *

global buffer_

buffer_ = []
img_exts = ['png', 'jpg', 'jpeg', 'bmp']

def mk_con(ip_, usn_, pwd_, secure_ = True):
	if secure_:
		con = ftplib.FTP_TLS()
		con.connect(ip_)
		con.login(usn_, pwd_)
		con.prot_p()
	else:
		con = ftplib.FTP()
		con.connect(ip_)
		con.login(usn_, pwd_)
	return con

def clear_buffer():
	global buffer_
	buffer_ = []

def cb_buffer(x):
	global buffer_
	buffer_.append(x)

def get_buffer():
	global buffer_
	return copy(buffer_)

class ftpFile(object):
	"""descript a ftp file"""
	def __init__(self, con, url = '/', mod = 'drwxrwxrwx', parent = None):
		super(ftpFile, self).__init__()
		self.url = url
		self.mod = mod
		self.con = con
		self.__size = None
		self.__parent = parent
		self.__im = None
		self.__fn = None

	def is_dir(self):
		return self.mod[0]=='d'

	def is_file(self):
		return self.mod[0]=='-'

	def size(self, refresh = False):
		if self.__size is None or refresh:
			self.__size = self.con.size(self.url)
		else: return self.__size

	def is_img(self):
		return split('\.', self.url)[-1] in img_exts and self.is_file()

	def list(self):
		if self.is_dir() and self.canRead() and self.canExec():
			sub = []
			clear_buffer()
			ls = con.retrlines('LIST %s'%self.url, cb_buffer)
			lines = get_buffer()
			for i in lines:
				arr = split('[ \t\n\r]+', i)
				mod = arr[0]
				url = arr[-1]
				if self.url[-1]=='/':
					url = self.url + url
				else:
					url = self.url + '/' + url
				nf = ftpFile(self.con, url, mod, parent = self)
				sub.append(nf)
			return sub
		else:
			print 'cannot list:', self.is_dir(), self.canRead(), self.canExec()

	def canRead(self, admin=True):
		return self.mod[1]=='r' and admin or self.mod[7]=='r'

	def canWrite(self, admin=True):
		return self.mod[2]=='w' and admin or self.mod[8]=='w'

	def canExec(self, admin=True):
		return self.mod[3]=='x' and admin or self.mod[9]=='x'

	def release_tmp(self):
		if self.__fn is not None:
			try:
				os.system('rm %s'%self.__fn)
			except Exception as e:
				pass

	def __transfer(self):
		self.fd.write()

	@staticmethod
	def createTmpFile(item = None):
		fd, fn = tempfile.mkstemp()
		# print fd, fn
		if item is not None:
			item.__fn = fn
		return os.fdopen(fd, 'wb'), fn

	@staticmethod
	def __transfer(fd):
		def cb(x):
			fd.write(x)
			fd.flush()
		return cb

	def download(self, fd = None):
		if self.is_file():
			if fd is None:
				fd, fn = ftpFile.createTmpFile(self)
			self.con.retrbinary('RETR %s'%self.url, ftpFile.__transfer(fd))
			fd.close()

	def __str__(self):
		return self.mod + ' ' + self.url

	def parent(self):
		return self.__parent

	def imshow(self, refresh = False):
		self.__im = self.img(refresh)
		if self.__im is not None:
			cv2.imshow(self.url, self.__im)
			cv2.waitKey(0)
		else:
			print 'download failed.'

	def img(self, refresh = False):
		if self.is_img():
			try:
				tmp = cv2.imread(self.__fn)
				self.__im = tmp
			except Exception as e:
				pass
			if self.__im is None or refresh:
				self.download()
				self.__im = cv2.imread(self.__fn)
		return self.__im

def getQImg(im, sz = (1760, 990)):
	if im is None:
		exit(233)
	if sz is not None: im = cv2.resize(im, sz)
	im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
	im = array2qimage(im)
	return QPixmap.fromImage(im)

class IMGallery(QWidget):

	def __init__(self, data):
		super(IMGallery, self).__init__()
		self.data = data
		self.initGUI()

	def initGUI(self):
		self.resize(1920, 1000)
		self.move(0,0)
		self.setWindowTitle('IMGallery')

		prevButton = QPushButton('Prev')
		nextButton = QPushButton('Next')
		disButton = QPushButton('/')
		self.prevButton = prevButton
		self.nextButton = nextButton
		self.disButton = disButton

		self.imgLabel = QLabel()
		# print dir(self.imgLabel)
		self.imgLabel.setMinimumWidth(1600)
		self.imgLabel.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignHCenter)
		self.ind = 0

		vbox = QVBoxLayout()
		vbox.addStretch(1)
		vbox.addWidget(disButton)
		vbox.addWidget(prevButton)
		vbox.addWidget(nextButton)

		hbox = QHBoxLayout()
		# hbox.addStretch(1)
		# hbox.setWidth(1800)
		# print dir(hbox)
		hbox.addWidget(self.imgLabel)
		hbox.addLayout(vbox)

		self.setLayout(hbox)

		self.prevButton.clicked.connect(self.S_prev)
		self.nextButton.clicked.connect(self.S_next)
		self.disButton.clicked.connect(self.S_fromhead)

		return self

	def refresh(self):
		self.setWindowTitle('IMGallery' + '  -  ' + self.data[self.ind].url)
		im = self.data[self.ind].img()
		im = getQImg(im, sz = None)
		self.imgLabel.setPixmap(im)
		self.disButton.setText('%d/%d'%(self.ind, len(self.data)))

	def show(self):
		super(IMGallery, self).show()
		self.refresh()
		return self

	def S_prev(self):
		self.ind -= 1
		self.ind = max(self.ind, 0)
		self.refresh()

	def S_next(self):
		self.ind += 1
		self.ind = min(self.ind, len(self.data)-1)
		self.refresh()

	def S_fromhead(self, offset = 0):
		self.ind = offset
		self.refresh()

	def keyPressEvent(self, e):
		# print e.key()
		# print [(i,QtCore.Qt.__dict__[i]) for i in dir(QtCore.Qt) if i[:4]=='Key_']
		if e.key() == QtCore.Qt.Key_A or e.key() == QtCore.Qt.Key_W:
			self.S_prev()
		if e.key() == QtCore.Qt.Key_S or e.key() == QtCore.Qt.Key_D:
			self.S_next()
		if e.key() == QtCore.Qt.Key_PageUp:
			for i in range(25):
				self.S_prev()
		if e.key() == QtCore.Qt.Key_PageDown:
			for i in range(25):
				self.S_next()


if __name__=='__main__':

	con = mk_con('ftp://ip:port', '@user', '#password', secure_ = False)
	root = ftpFile(url = '/location', con = con)
	# root = ftpFile(url = '/fengweitao/Siamese_FC/train/', con = con)

	data = []
	ls = root.list()
	for ii, i in enumerate(ls):
		print 'searching [%.2f%%]'%(100.*(ii+1)/len(ls)),i,
		if i.is_img():
			# i.download()
			data.append(i)
			print 'Hits'
			# i.imshow()
		else: print ''

	app = QApplication(sys.argv)
	content = IMGallery(data).show()
	ret_code = app.exec_()

	con.close()

	for i in data:
		i.release_tmp()

	exit(ret_code)
