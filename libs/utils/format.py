from libs.utils.imports import *

def convert_to_unix_time(date_str, format_str):
	parsed_date = datetime.strptime(date_str, format_str)
	unix_time = int(time.mktime(parsed_date.timetuple()))
	return unix_time

def format_time_ago(date_str, format_str):
	date = datetime.strptime(date_str, format_str)
	if date.tzinfo is None or date.tzinfo.utcoffset(date) is None:
		date = pytz.utc.localize(date)
	now = datetime.now(timezone.utc)
	time_diff = now - date
	
	years = time_diff.days // 365
	months = time_diff.days // 30
	weeks = time_diff.days // 7
	days = time_diff.days
	hours = time_diff.seconds // 3600
	minutes = (time_diff.seconds % 3600) // 60
	seconds = time_diff.seconds % 60
	
	if years > 0:
		if months >= 6: years += 1
		decades = floor(years/10)
		centuries = floor(decades/10)
		if centuries > 0:
			return f"{centuries} centurie{'s' if centuries > 1 else ''}"
		elif decades > 0:
			return f"{decades} decade{'s' if decades > 1 else ''}"
		return f"{years} year{'s' if years > 1 else ''}"
	elif months > 0:
		if days >= 15: # rougly half a month
			months += 1
			if months == 12: return '1 year'
		return f"{months} month{'s' if months > 1 else ''}"
	elif weeks > 0:
		if days >= 4: # round up if friday, saturday or sunday
			weeks += 1
			if weeks == 4: return '1 month' # roughly a month
		return f"{weeks} week{'s' if weeks > 1 else ''}"
	elif days > 0:
		if hours >= 12:
			days += 1
			if days == 7: return '1 week'
		return f"{days} day{'s' if days > 1 else ''}"
	elif hours > 0:
		if minutes >= 30:
			hours += 1
			if hours == 24: return '1 day'
		return f"{hours} hour{'s' if hours > 1 else ''}"
	elif minutes > 0:
		if seconds >= 30:
			minutes += 1
			if minutes == 60: return '1 hour'
		return f"{minutes} minute{'s' if minutes > 1 else ''}"
	else:
		return f"{seconds} second{'s' if seconds > 1 else ''}"

def code_to_txt(code):
	return code.replace('   ', '\\t').replace('''
''', '\\n')

def txt_to_code(code):
	code.replace('\\\\t', '\\t')
	code.replace('\\\\n', '\\n')
	return code.replace('\\t', '    ').replace('\\n', '''
''')