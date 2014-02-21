import sublime
import sublime_plugin
import dircache
import os
import tempfile
import popen2
import threading
import time
import json



class RemoteCompileCommand(sublime_plugin.WindowCommand):

	def printMsg(self, msg):
		t = time.time()
		_time = time.strftime('%H:%M:%S', time.localtime(t))
		print "{0}  [RemoteCompile]{1}".format(_time, msg)



	def getProjectFile(self):
		_files = dircache.listdir(self.lPath)
		for f in _files:
			_name,_ext = os.path.splitext(f)
			if(_ext==".sublime-project"):
				return f

		return ""


	def getProjectPath(self):
		_f = sublime.active_window().active_view().file_name()
		for d in sublime.active_window().folders():
			_tmpdir = os.path.join(d)
			if(_f.find(_tmpdir)==0):
				return _tmpdir
			
		return ""


	def run(self):

		self.lPath = self.getProjectPath()
		if(self.lPath==""):
			self.printMsg("can't find project's path")
			return


		_projectFileName = os.path.join(self.lPath, self.getProjectFile());
		if(self.lPath==""):
			self.printMsg("can't find project's file")
			return


		try:
			_projectfd = open(_projectFileName,"r")
			_json = json.loads( _projectfd.read())
			_projectfd.close()
		
			_default	= _json["remote_compile"]["default"]
			self.host 	= _json["remote_compile"][_default]["host"]
			self.port 	= _json["remote_compile"][_default]["port"]
			self.user	= _json["remote_compile"][_default]["username"]
			self.passwd = _json["remote_compile"][_default]["password"]
			self.cmd 	= _json["remote_compile"][_default]["cmd"]
			self.rPath 	= _json["remote_compile"][_default]["remote_path"]
			self.packagepath = os.path.join(sublime.packages_path(), "RemoteCompile")

		except:
			self.printMsg("setting error")
			return
		

		self.printMsg("starting.....")
		self.running = True
		self.status = "Remote compiling"


		sublime.set_timeout(self.refreshStatus, 0)

		_t = threading.Thread(target=self.runProc)
		_t.start()
		#_t.join()



	def refreshStatus(self):

		if(self.running):
			if(len(self.status)>=30):
				self.status = "Remote compiling"
			else:
				self.status = self.status + "."

			sublime.status_message(self.status)
			sublime.set_timeout(self.refreshStatus, 100)
		else:
			sublime.status_message("Remote compile finished")			





	def runProc(self):

		self.arrSTDIN = []
		self.arrSTDER = []
		self.arrFiles = []

		self.printMsg("uploading....")
		self.recurrenceDir(self.lPath, self.rPath)
		self.generateBatch()
		self.execPsftp()
		
		self.printMsg("compiling....")
		self.sshCommand( self.cmd )

		self.printMsg("finished")
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
		self.running = False
		# sublime.status_message("finished")



	def sshCommand(self, cmd):

		os.chdir(self.packagepath)
		_cmd = "plink -ssh " + self.host + " -P " + self.port + " -l " + self.user + " -pw " + self.passwd + " cd " + self.rPath + "; " + cmd
		#print _cmd
		r, w, e = popen2.popen3(_cmd)
		for l in r.readlines():
			self.arrSTDIN.append(l)

		for l in e.readlines():
			self.arrSTDER.append(l)



	def execPsftp(self):

		os.chdir(self.packagepath)
		_cmd = "psftp -P " + self.port + " " + self.user + "@" + self.host + " -pw " + self.passwd + " -C -b \"" + self.tmpfile.name + "\" -be"
		r, w, e = popen2.popen3(_cmd)
		for l in r.readlines():
			self.arrSTDIN.append(l)

		for l in e.readlines():
			self.arrSTDER.append(l)

		os.unlink(self.tmpfile.name)



	def generateBatch(self):
	
		self.tmpfile = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', prefix='batch_', dir=self.packagepath, delete=False)
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

			_fullL = os.path.join(lpath, f)
			#if ignore
				#continue

			if os.path.isdir(_fullL):
				_dirTmp.append(f)
			else:
				self.arrFiles.append( "put \"" + f + "\"" )


		for d in _dirTmp:
			self.recurrenceDir(	os.path.join(lpath,d), rpath + "/" +d )

