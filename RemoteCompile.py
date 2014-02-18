import sublime, sublime_plugin
import dircache, os



class RemoteCompileCommand(sublime_plugin.TextCommand):

    def run(self, edit):
    	self.workPath = ".\\"
    	self.arrFiles = []

    	self.recurrenceDir(self.workPath)

    	for l in self.arrFiles:
    		print l



    def recurrenceDir(self, path):
		_files = dircache.listdir(path)
		for f in _files:
			if f=="." or f=="..":
				continue

			#if ignore
				#continue

			_full = os.path.join(path,f)

			if os.path.isdir(_full):
				self.recurrenceDir(_full)	
			else:
				self.arrFiles.append( _full )
	

	def recurrenceDir2(self):
		print "A"
	
	#def generateBatch(self):
	#	pass
		#for l in self.arrFiles:
    	#	print l


