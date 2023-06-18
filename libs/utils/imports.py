import os, time, inspect, json, urllib.parse, platform, re, threading, sys, importlib, glob, requests
from pprint import pprint
from datetime import datetime, timezone
from math import *

# try:
# 	from parsel import Selector
# except:
# 	os.system('pip install parsel')
# 	from parsel import Selector
# try:
# 	import pytz
# except:
# 	os.system('pip install pytz')
# 	import pytz
try:
	import Levenshtein
except:
	os.system('pip install levenshtein')
	import Levenshtein
try:
	from bs4 import BeautifulSoup
except:
	os.system('pip install beautifulsoup4')
	from bs4 import BeautifulSoup