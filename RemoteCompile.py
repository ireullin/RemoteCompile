import sublime
import sublime_plugin
import dircache
import os
import tempfile
import popen2
import threading
import time
import json
import hashlib


class RemoteCompileCommand(sublime_plugin.TextCommand):

	def printMsg(self, msg):
		t = time.time()
		_time = time.strftime('%H:%M:%S', time.localtime(t))
		print "{0}  [RemoteCompile] {1}".format(_time, msg)



	def getProjectFile(self, path):
		_files = dircache.listdir(path)
		for f in _files:
			_name,_ext = os.path.splitext(f)
			if(_ext==".sublime-project"):
				return os.path.join(path, f)

		return ""



	def getProjectPath(self):
		_f = sublime.active_window().active_view().file_name()
		if(_f==None):
			return ""
			
		for d in sublime.active_window().folders():
			_tmpdir = os.path.join(d)
			if(_f.find(_tmpdir)==0):
				return _tmpdir
			
		return ""



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



	def getIgnoreFile(self):

		_filePath = os.path.join(self.lPath, self.ignore)

		if( os.path.isfile(_filePath)==False ):
			return

		_fd = open(_filePath ,"r")
		for l in _fd:
			if(l[0]=="*"):
				self.arrIgnores.append( l.rstrip('\n').rstrip('\r')   )
			else:
				_name = os.path.join(self.lPath, l)
				self.arrIgnores.append( _name.replace('/','\\').rstrip('\n').rstrip('\r')  )

		_fd.close()
		#print self.arrIgnores
			


	def getFileMD5(self, filename):

		_f = open(filename,"rb")
		_md5 = hashlib.md5( _f.read() ).hexdigest()
		_f.close()
		return _md5



	def getHashMD5(self, filename):
		_hash = {}
		if(os.path.isfile(filename)==False):
			return _hash

		_f = open(filename, "r")
		for l in _f :
			_l = l.rstrip('\n').rstrip('\r')
			_hash[_l] = ""

		return _hash



	def readToJson(self, filename):
		_fd = open(filename,"r")
		_json = json.loads( _fd.read())
		_fd.close()
		return _json



	def writeToJson(self, filename, jsonStr):
		_fd = open(filename,"w")
		_fd.write( json.dumps( jsonStr, indent=4 ))
		_fd.close()



	def run(self, edit, **args):

		self.lPath = self.getProjectPath()
		if(self.lPath==""):
			self.printMsg("this file is not in the project")
			sublime.error_message("this file is not in the project")
			return


		_projectFileName = self.getProjectFile(self.lPath);
		if(self.lPath==""):
			self.printMsg("can't find file project")
			sublime.error_message("can't find file project")
			return


		try:
			_json = self.readToJson(_projectFileName)

			_default	= _json["remote_compile"]["default"]
			self.host 	= _json["remote_compile"][_default]["host"]
			self.port 	= _json["remote_compile"][_default]["port"]
			self.user	= _json["remote_compile"][_default]["username"]
			self.passwd = _json["remote_compile"][_default]["password"]
			self.cmd 	= _json["remote_compile"][_default]["cmd"]
			self.rPath 	= _json["remote_compile"][_default]["remote_path"]
			self.ignore = _json["remote_compile"][_default]["ignore"]

			self.compiling	= args["compiling"]
			self.uploading	= args["uploading"]
			self.comparing	= args["comparing"]
			self.packagepath= os.path.join(sublime.packages_path(), "RemoteCompile")

		except:
			self.printMsg("setting error")
			sublime.error_message("setting error")
			return
		

		self.printMsg("starting.....")
		self.running = True
		self.status = "Remote compiling"

		sublime.set_timeout(self.refreshStatus, 0)

		_t = threading.Thread(target=self.runProc)
		_t.start()
		#_t.join()

	

	def runProc(self):

		self.arrSTDIN = []
		self.arrSTDER = []
		self.arrFiles = []
		self.arrIgnores = []
		self.hMD5new = {}
		self.hMD5old = {}


		_md5path = os.path.join( self.lPath, ".md5")

		if(self.comparing.lower()=="true" and os.path.isfile(_md5path)==True ):
			self.hMD5old = self.readToJson(_md5path)


		if(self.uploading.lower()=="true"):
			self.printMsg("uploading....")
			self.getIgnoreFile()
			self.recurrenceDir(self.lPath, self.rPath)
			self.generateBatch()
			self.execPsftp()
			self.writeToJson(_md5path, self.hMD5new)


		if(self.compiling.lower()=="true"):
			self.printMsg("compiling....")
			self.sshCommand( self.cmd )


		self.printMsg("finished")
		sublime.set_timeout(self.callbackResult, 0)
		


	def callbackResult(self):

		t = time.time()
		_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t))
		
		#_view = self.window.new_file()
		_filePath = os.path.join(self.packagepath, "compile report")
		
		_f = open(_filePath,"w")
		
		_f.write("finished time " + _time + "\n\n")	

		_f.write("====== STANDARD ERROR ======\n\n")
		for l in self.arrSTDER:
			_f.write(l)

		_f.write("\n\n\n")

		_f.write("====== STANDARD OUTPUT ======\n\n")		
		for l in self.arrSTDIN:
			_f.write(l)

		_f.close()

		_view = sublime.active_window().open_file(_filePath)
		#_view.set_name("compile report " + _time )


		"""
		_edit = _view.begin_edit()
		
		_buff = "".join(self.arrSTDIN)
		_view.insert(_edit, 0, _buff.decode('utf-8') )
		_view.insert(_edit, 0, "\n")
		_view.insert(_edit, 0, "====== STANDARD OUTPUT ======\n")
		_view.insert(_edit, 0, "\n\n\n")

		_buff = "".join(self.arrSTDER)
		_view.insert(_edit, 0, _buff.decode('utf-8') )
		_view.insert(_edit, 0, "\n")
		_view.insert(_edit, 0, "====== STANDARD ERROR ======\n")

		_view.end_edit(_edit)
		"""

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
	
		self.tmpfile = tempfile.NamedTemporaryFile(mode='w', suffix='.tmp', prefix='batch_', dir=self.packagepath, delete=False)
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
			if(f[0]=="."): # mean ".", "..", and hidden file
				continue

			_fullL = os.path.join(lpath, f)
			if(self.isIgnored(_fullL)):
				continue

			if os.path.isdir(_fullL):
				_dirTmp.append(f)
			else:
				_md5 = self.getFileMD5(_fullL)
				self.hMD5new[_fullL] = _md5

				if(  self.hMD5old.has_key(_fullL)==True and self.hMD5old[_fullL]==_md5 ):
					pass
				else:
					self.arrFiles.append( "put \"" + f + "\"" )


		for d in _dirTmp:
			self.recurrenceDir(	os.path.join(lpath,d), rpath + "/" +d )


		

	def isIgnored(self, fullPath):
		if(len(self.arrIgnores)==0):
			return False

		for l in self.arrIgnores:

			if(l[0]=="*"):
				_name1,_ext1 = os.path.splitext(l)
				_name2,_ext2 = os.path.splitext(fullPath)
				if _ext1 == _ext2 :
					return True
			else:
				if fullPath == l :
					return True

		return False

