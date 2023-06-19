import json, inspect

def print_var(var):
	callers_local_vars = inspect.currentframe().f_back.f_locals.items()
	pprint(str([k for k, v in callers_local_vars if v is var][0])+' = '+str(var), indent=3)
	print()

def print_json(obj, indent=3):
	if not type(obj) is dict: obj = json.loads(obj)
	if type(obj) is str:
		obj = json.loads(obj)
	print(json.dumps(obj, indent=indent))

BLACK, RED, GREEN, YELLOW, BLUE, PURPLE, CYAN, WHITE, ORANGE = 30, 31, 32, 33, 34, 35, 36, 37, 38
# in case not all was imported (from debug import *)
color_codes = {
	'black': 30,
	'red': 31,
	'green': 32,
	'yellow': 33,
	'blue': 34,
	'purple': 35,
	'cyan': 36,
	'white': 37,
	'orange': 38
}
# make it work for windows?
def cprint(string, color=30, end='\n'):
	if type(color) is str: color = color_codes.get(color.lower())
	if color:
		print(f"\033[{color}m{string}\033[0m", end=end)
	else:
		print('cprint: Unknown color, available colors are:\n')
		print_json(color_codes)

def print_all_attributes(obj):
	for attr, value in obj.__iter__():
		print(f'{attr} = {value}\n\n')

def print_all_items(obj):
	for key, value in obj.items():
		print(f'{key} = {value}\n\n')

from libs.utils.web import status_code_text, status_code_category, status_code_category_color

try:
	from bs4 import BeautifulSoup
except:
	os.system('pip install beautifulsoup4')
	from bs4 import BeautifulSoup

def print_response(r, indent=3):

	headers = {}
	for key, value in r.headers.items():
		headers[key] = value
	saved_response = {
		# "_content": r._content.decode('utf-8'),
		"_content_consumed": str(r._content_consumed),
		"_next": str(r._next),
		"status_code": str(r.status_code),
		"headers": headers,
		"url": str(r.url),
		"encoding": str(r.encoding),
		"history": str(r.history),
		"reason": str(r.reason),
		"elapsed": str(r.elapsed)
	}

	print(json.dumps(saved_response, indent=indent))
	if r._content != b'':
		
		# decode

		content_encoding = None
		content_encoding_in_headers = True
		if 'Content-Encoding' in headers: content_encoding = 'Content-Encoding'
		elif 'content-encoding' in headers: content_encoding = 'content-encoding'
		else: content_encoding_in_headers = False

		if content_encoding in headers:
			if 'gzip' in headers[content_encoding] or 'compress' in headers[content_encoding] or 'deflate' in headers[content_encoding]:
				content = zlib.decompress(r._content)
			elif 'br' in headers[content_encoding]:
				# content = brotli.decompress(r._content) fails :c
				content = r._content.decode('utf-8', 'ignore')
		else:
			content = r._content.decode('utf-8', 'ignore')

		# format and print
		
		content_type = None
		content_type_in_headers = True
		if 'Content-Type' in headers: content_type = 'Content-Type'
		elif 'content-type' in headers: content_type = 'content-type'
		else: content_type_in_headers = False

		if content_type_in_headers:
			if 'text/plain' in headers[content_type]:
				print(content)
			elif 'text/html' in headers[content_type]:
				print(BeautifulSoup(content, 'html.parser').prettify(indent_width=indent))
			elif 'application/json' in headers[content_type]:
				print(json.dumps(json.loads(content), indent=indent))
			elif 'application/x-www-form-urlencoded' in headers[content_type]:
				print(decode_url(content))
		else:
			print(content)