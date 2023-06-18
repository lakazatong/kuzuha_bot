from libs.utils.imports import *
from libs.utils.web import status_code_text

# make it work for windows?
BLACK, RED, GREEN, YELLOW, BLUE, PURPLE, CYAN, WHITE = 30, 31, 32, 33, 34, 35, 36, 37
def cprint(string, color_code=30, end='\n'):
	print(f"\033[{color_code}m{string}\033[0m", end=end)

def print_var(var):
	callers_local_vars = inspect.currentframe().f_back.f_locals.items()
	pprint(str([k for k, v in callers_local_vars if v is var][0])+' = '+str(var), indent=3)
	print()

def print_json(obj, indent=3):
	if type(obj) is str:
		obj = json.loads(obj)
	print(json.dumps(obj, indent=indent))

def print_all_attributes(obj):
	for attr, value in obj.__iter__():
		print(f'{attr} = {value}\n\n')

def print_all_items(obj):
	for key, value in obj.items():
		print(f'{key} = {value}\n\n')

def report_request_error(r, headers=None, content=None):
	if not headers:	headers = r.headers
	if not content:	content = r.content
	if not type(headers) is dict: headers = json.loads(r.headers) if type(r.headers) in [str, bytes, bytearray] else dict(r.headers)
	if not type(content) is dict: content = json.loads(r.content) if type(r.content) in [str, bytes, bytearray] else dict(r.content)
	err = {
		"status_code": r.status_code,
		"status_code_text": status_code_text(r.status_code),
		"headers": headers,
		"content": content
	}
	print()
	cprint('request error', RED)
	print('response = ', end='')
	print_json(err)