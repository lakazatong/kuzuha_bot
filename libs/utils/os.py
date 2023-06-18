from libs.utils.imports import *

def from_windows():
	return platform.system() == 'Windows'

_exit = exit
def exit_with_function(code, exit_function=None):
	if exit_function:
		try: exit_function()
		except: pass
	_exit(code)

def split_path(path):
	return os.path.split(path)

def run(func, delay):
	timer = threading.Timer(delay, func)
	timer.start()
	return timer