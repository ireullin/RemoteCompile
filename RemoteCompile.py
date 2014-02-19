import sublime
import sublime_plugin
import dircache
import os
import tempfile
import popen2
import threading
import time


class RemoteCompileCommand(sublime_plugin.WindowCommand):

	def run(self):
		print "starting remote compile....."
		_t = threading.Thread(target=self.runProc)
		_t.start()
		#_t.join()

		

	def runProc(self):

		self.host = "172.16.10.141"
		self.port = "1104"
		self.user = "root"
		self.passwd = "Uitox!!)$"
		self.cmd = "sh ./compile.sh"

		self.rPath = "/var/test"
		self.lPath = "C:\\MyDocument\\git\\MyLib"

		self.arrSTDIN = []
		self.arrSTDER = []
		self.arrFiles = []

		print "preparing files...."
		self.recurrenceDir(self.lPath, self.rPath)
		
		print "uploading...."
		self.generateBatch()
		self.execPsftp()
		
		print "compiling...."
		self.sshCommand( self.cmd )

		print "finished"
		sublime.set_timeout(self.callbackResult, 0)
		
    	

	def callbackResult(self):
		t = time.time()
		_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t))
		
		_view = self.window.new_file()
		_view.set_name("compile report " + _time )

		_edit = _view.begin_edit()
		
		_buff = "".join(self.arrSTDIN)
		_view.insert(_edit, 0, _buff)
		_view.insert(_edit, 0, "====== STANDARD OUTPUT ======\n")
		_view.insert(_edit, 0, "\n\n")

		_buff = "".join(self.arrSTDER)
		_view.insert(_edit, 0, _buff)
		_view.insert(_edit, 0, "====== STANDARD ERROR ======\n")



		_view.end_edit(_edit)
		sublime.status_message("finished")

	def sshCommand(self, cmd):
		_cmd = "plink -ssh " + self.host + " -P " + self.port + " -l " + self.user + " -pw " + self.passwd + " cd " + self.rPath + "; " + cmd
		print _cmd
		r, w, e = popen2.popen3(_cmd)
		for l in r.readlines():
			self.arrSTDIN.append(l)

		for l in e.readlines():
			self.arrSTDER.append(l)


	def execPsftp(self):

		_cmd = "psftp -P " + self.port + " " + self.user + "@" + self.host + " -pw " + self.passwd + " -C -b \"" + self.tmpfile.name + "\" -be"
		r, w, e = popen2.popen3(_cmd)
		for l in r.readlines():
			self.arrSTDIN.append(l)

		for l in e.readlines():
			self.arrSTDER.append(l)

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

