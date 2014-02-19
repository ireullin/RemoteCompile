import sublime
import sublime_plugin
import dircache
import os
import tempfile
import popen2
import threading


class RemoteCompileCommand(sublime_plugin.TextCommand):

	def run(self, edit):
		print "starting remote compile....."
		_t = threading.Thread(target=self.runProc)
		_t.start()
		#_t.join()


	def runProc(self):

		self.host = "172.16.10.141"
		self.port = "1104"
		self.user = "root"
		self.passwd = "Uitox!!)$"

		self.rPath = "/var/test"
		self.lPath = "C:\\Users\\tech0039\\AppData\\Roaming\\Sublime Text 2\\Packages\\RemoteCompile"

		self.arrFiles = []
		self.recurrenceDir(self.lPath, self.rPath)
		self.generateBatch()
		self.execPsftp()
    	

	def execPsftp(self):

		_cmd = "psftp -P " + self.port + " " + self.user + "@" + self.host + " -pw " + self.passwd + " -C -b \"" + self.tmpfile.name + "\" -be"
		r, w, e = popen2.popen3(_cmd)
		for l in r.readlines():
			print l

		os.unlink(self.tmpfile.name)

	def generateBatch(self):
	
		self.tmpfile = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', prefix='batch_', dir=self.lPath, delete=False)
		#_f = open("tmpfile.batch", "w") # for debug

		for l in self.arrFiles:
			self.tmpfile.write(l + "\n")
		
		self.tmpfile.write("\n")
		self.tmpfile.write("bye\n")
		self.tmpfile.close()

		


	def recurrenceDir(self, lpath, rpath):
		
		self.arrFiles.append("")
		self.arrFiles.append( "lcd \"" + lpath + "\"" )
		self.arrFiles.append( "mkdir \"" + rpath + "\"" )
		self.arrFiles.append( "cd \"" + rpath + "\"" )


		_dirTmp = []
		#print lpath
		_files = dircache.listdir(lpath)
		for f in _files:
			if f=="." or f=="..":
				continue

			_fullL = lpath + "\\" + f
			#if ignore
				#continue

			if os.path.isdir(_fullL):
				_dirTmp.append(f)
			else:
				self.arrFiles.append( "put \"" + f + "\"" )


		for d in _dirTmp:
			self.recurrenceDir(	lpath + "\\" + d, rpath + "/" +d )

