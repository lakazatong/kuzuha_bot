import requests
from funcs import *

v1, v2 = None, None
modes = {
	'osu': 0,
	'taiko': 1,
	'ctb': 2,
	'mania': 3
}

def extract_user_data(data):
	user = json.loads(data)
	# save_json(user, '../tests/test_raw.json')
	ssh_count = user['statistics']['grade_counts']['ssh']
	ss_count = user['statistics']['grade_counts']['ss']
	sh_count = user['statistics']['grade_counts']['sh']
	s_count = user['statistics']['grade_counts']['s']
	a_count = user['statistics']['grade_counts']['a']
	info = {
		"username": user['username'],
		"playmode": user['playmode'],
		"avatar_url": user['avatar_url'],
		"country_code": user['country_code'],
		# "country_svg_flag_url": 'https://osu.ppy.sh' + sel.xpath('/html/body/div[3]/div[3]/div/div[3]/div[7]/ul/li[13]/a/span/div/@style').get().split(':')[1][6:-3],
		"bancho_rank": user['statistics']['global_rank'] if user['statistics']['global_rank'] != None else '-',
		
		"country_rank": user['statistics']['country_rank'] if 'country_rank' in user['statistics'] else None,
		"peak_rank": user['rank_highest']['rank'] if user['rank_highest'] != None else None,
		"peak_rank_achieved": convert_to_unix_time(user['rank_highest']['updated_at'], '%Y-%m-%dT%H:%M:%SZ') if user['rank_highest'] != None else None,

		"level": user['statistics']['level']['current'],
		"level_progress": user['statistics']['level']['progress'],
		"pp": user['statistics']['pp'],
		"acc": user['statistics']['hit_accuracy'],
		"playcount": user['statistics']['play_count'],
		"playcount_hours": round(user['statistics']['play_time']/3600),
		"ranks": [
			ssh_count,
			ss_count,
			sh_count,
			s_count,
			a_count
		],
		"ranks_all_zero": ssh_count == 0 and ss_count == 0 and sh_count == 0 and s_count == 0 and a_count == 0,
		"last_seen": format_time_ago(user['last_visit'], '%Y-%m-%dT%H:%M:%S%z'),
		"is_online": user['is_online'],
		"is_verified": user['discord'] != None
	}
	return info

# --------------------------------------------------------------------------- #

# if v2 can't fulfill the request
class OsuAPI_v1:

	def __init__(self):
		with open('../secrets/osu_api_v1_key', 'r') as f:
			self.key = f.read()

	def user_recents(self, username, mode, limit):
		return json.loads(requests.request('GET', f'https://osu.ppy.sh/api/get_user_recent?k={self.key}&u={username}&m={modes[mode]}&limit={limit}').content)

	def user_recent(self, username, mode):
		return self.user_recents(username, mode, 1)

# --------------------------------------------------------------------------- #

# priority on v2
class OsuAPI_v2:

	token_headers = {
		"Accept": "application/json",
		"Content-Type": "application/x-www-form-urlencoded"
	}
	json_headers = {
		"Accept": "application/json",
		"Content-Type": "application/json",
	}
	urlencoded_headers = { 
		"Accept": "application/json",
		"Content-Type": "application/x-www-form-urlencoded",
	}

	def update_tokens(self, response):
		self.refresh_token = response['refresh_token']
		with open('../secrets/osu_api_v2_refresh_token', 'w+') as f:
			f.write(self.refresh_token)
		self.json_headers['Authorization'] = response['token_type'] + ' ' + response['access_token']
		self.urlencoded_headers['Authorization'] = response['token_type'] + ' ' + response['access_token']
		run(self.refresh_tokens, delay=int(response['expires_in']))

	def first_manual_startup(self):
		url = f'https://osu.ppy.sh/oauth/authorize?client_id={self.client_id}&redirect_uri={self.redirect_uri}&response_type=code&scope=public+identify&state=randomval'
		if from_windows():
			import webbrowser
			webbrowser.open(url)
		else:
			# escape the '&' characters
			url = url.replace('&', '^&')
			os.system(f'cmd.exe /C "start {url}"')
		code = input('Enter the received code contained in the url after Authorizing:\n')
		data = f'client_id={self.client_id}&client_secret={self.client_secret}&code={code}&grant_type=authorization_code&redirect_uri={self.redirect_uri}'
		response = json.loads(requests.request('POST', 'https://osu.ppy.sh/oauth/token', headers=self.urlencoded_headers, data=data).content)
		self.update_tokens(response)

	def refresh_tokens(self):
		print('v2: refreshing token... ', end='')
		response = json.loads(requests.request('POST', 'https://osu.ppy.sh/oauth/token', headers=self.token_headers, data=f'client_id={self.client_id}&client_secret={self.client_secret}&grant_type=refresh_token&refresh_token={self.refresh_token}&scope=public+identify').content)
		self.update_tokens(response)
		cprint('done', GREEN)

	def __init__(self):
		# init constants
		self.client_id = '22868'
		with open('../secrets/osu_api_v2_client_secret', 'r') as f:
			self.client_secret = f.read()
		self.redirect_uri = r'http%3A%2F%2Fdiscord%2Ecom'

		# get token
		if os.path.exists('../secrets/osu_api_v2_refresh_token'):
			with open('../secrets/osu_api_v2_refresh_token', 'r') as f:
				self.refresh_token = f.read()
			self.refresh_tokens()
		else:
			self.first_manual_startup()

	def user_info(self, username, mode):
		r = requests.request('GET', f'https://osu.ppy.sh/api/v2/users/{username}/{mode}', headers=self.json_headers)
		return extract_user_data(r.content) if r.status_code == 200 else None

	def user_exists(self, username, mode):
		return requests.request('GET', f'https://osu.ppy.sh/api/v2/users/{username}/{mode}', headers=self.json_headers).status_code == 200

# --------------------------------------------------------------------------- #

# call v1 or v2 as needed
class OsuAPI:

	def __init__(self):
		global v1, v2
		v1 = OsuAPI_v1()
		v2 = OsuAPI_v2()

	def user_info(self, username, mode='osu'):
		return v2.user_info(username.replace(' ', '%20'), mode)

	def user_exists(self, username):
		return v2.user_exists(username.replace(' ', '%20'), 'osu')

	def user_recents(self, username, mode=None, limit=5):
		return v1.user_recents(username.replace(' ', '%20'), mode if mode else v2.user_info(username, 'osu')['playmode'], limit)

	def user_recent(self, username, mode=None):
		return v1.user_recent(username.replace(' ', '%20'), mode if mode else v2.user_info(username, 'osu')['playmode'])