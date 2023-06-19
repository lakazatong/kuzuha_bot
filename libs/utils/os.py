import os, threading, platform

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

from libs.utils.debug import cprint

def read_file(path, mode='r'):
	r = None
	if os.path.exists(path):
		try:
			with open(path, mode) as f:
				r = f.read()
		except:
			cprint('read_file: failed tp read '+path, 'red')
	return r