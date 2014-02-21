import sublime
import sublime_plugin
import dircache
import os
import time
import json


class GenerateExampleCommand(sublime_plugin.TextCommand):

	def run(self, edit):
		_path = self.getProjectPath()
		if(_path==""):
			self.printMsg("this file is not in the project")
			return


		_file = self.getProjectFile(_path)
		if(_file==""):
			self.printMsg("can't find file project")
			return

		
		_fd1 = open(_file,"r")
		_json = json.loads( _fd1.read())
		_fd1.close()


		_host1 = {}
		_host1["host"] = "host name"
		_host1["port"] = "22"
		_host1["username"] = "root"
		_host1["password"] = "1234"
		_host1["cmd"] = "shell or make"
		_host1["remote_path"] = "/var/tmp"
		_host1["ignore"] = "as .gitignore"

		_rc = {}
		_rc["default"] = "host_1"
		_rc["host_1"] = _host1

		_json["remote_compile"] = _rc
		

		#print json.dumps( _json, indent=4 )
		_fd2 = open(_file,"w")
		_fd2.write( json.dumps( _json, indent=4 ))
		_fd2.close()

		sublime.active_window().open_file(_file)

		self.printMsg("generated")



	def printMsg(self, msg):
		t = time.time()
		_time = time.strftime('%H:%M:%S', time.localtime(t))
		print "{0}  [RemoteCompile]{1}".format(_time, msg)


	def getProjectFile(self, path):
		_files = dircache.listdir(path)
		for f in _files:
			_name,_ext = os.path.splitext(f)
			if(_ext==".sublime-project"):
				return os.path.join(path, f)

		return ""


	def getProjectPath(self):
		_f = sublime.active_window().active_view().file_name()
		for d in sublime.active_window().folders():
			_tmpdir = os.path.join(d)
			if(_f.find(_tmpdir)==0):
				return _tmpdir
			
		return ""



