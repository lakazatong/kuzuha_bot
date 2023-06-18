from libs.utils.all import *
# source : https://github.com/Francesco149/pyttanko/blob/master/pyttanko.py
from libs.pyttanko import *

v1, v2 = None, None
def exit_function():
	v1.close()
	v2.close()
def exit(code=0):	
	exit_with_function(code, exit_function)

def extract_user_data(user):
	ssh_count = user['statistics']['grade_counts']['ssh']
	ss_count = user['statistics']['grade_counts']['ss']
	sh_count = user['statistics']['grade_counts']['sh']
	s_count = user['statistics']['grade_counts']['s']
	a_count = user['statistics']['grade_counts']['a']
	info = {
		"id": user['id'],
		"username": user['username'],
		"playmode": user['playmode'],
		"avatar_url": user['avatar_url'],
		"country_code": user['country_code'],
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
		"last_seen": format_time_ago(user['last_visit'], '%Y-%m-%dT%H:%M:%S%z') if user['last_visit'] else None,
		"is_online": user['is_online'],
		"is_verified": user['discord'] != None
	}
	return info

def score_stats(user_score, beatmap_id, fc=False, max_combo=None):
	osu_file = v2.osu_file(beatmap_id)
	with open('test.txt', 'w+') as f:
		f.write(osu_file)
	p = parser()
	bmap = p.map(osu_file)
	mods = mods_from_str(''.join(user_score['mods']))
	stars = diff_calc().calc(bmap, mods)
	stats = user_score['statistics']
	if not max_combo: max_combo = bmap.max_combo()
	combo = user_score['max_combo']
	n300 = stats['count_300']
	n100 = stats['count_100']
	n50 = stats['count_50']
	nmiss = stats['count_miss']
	if fc:
		combo = max_combo
		n300 += stats['count_miss']
		nmiss = 0
	r = ppv2(aim_stars=stars.aim, speed_stars=stars.speed, mods=mods, combo=combo, n300=n300, n100=n100, n50=n50, nmiss=nmiss, bmap=bmap)
	pp = {
		"total": r[0],
		"aim": r[1],
		"speed": r[2],
		"acc": r[3]
	}
	stars = {
		"total": stars.total,
		"aim": stars.aim,
		"speed": stars.speed
	}
	r = {
		"pp": pp,
		"stars": stars,
		"max_combo": max_combo,
		"acc": r[4]
	}
	return r

def score_pp(user_score, beatmap_id, fc=False):
	return score_stats(user_score, beatmap_id, fc)['pp']['total']

def user_scores_sort_function(user_scores, key):
	r = sorted(user_scores, key=lambda x: x[key])
	if key == 'pass':
		r.reverse()
	elif key == 'rank':
		while not r[0]['rank'] in ['SSH', 'SS', 'SH', 'S']: r.append(r.pop(0))
	return r

# --------------------------------------------------------------------------- #

# if v2 can't fulfill the request
class OsuAPI_v1:

	mode_code = {
		'osu': 0,
		'taiko': 1,
		'ctb': 2,
		'mania': 3
	}

	def __init__(self):
		with open('secrets/osu_api_v1_key', 'r') as f:
			self.key = f.read()

	def user_recents(self, username, mode, limit):
		params = {
			"k": self.key,
			"u": username,
			"m": self.mode_code[mode],
			"limit": limit
		}
		build_get_url('https://osu.ppy.sh/api/get_user_recent', params)
		return json.loads(requests.request('GET', url).content)

	def user_recent(self, username, mode):
		return self.user_recents(username, mode, 1)

	def close(self):
		...

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

	def update_tokens(self, r):
		self.refresh_token = r['refresh_token']
		with open('secrets/osu_api_v2_refresh_token', 'w+') as f:
			f.write(self.refresh_token)
		self.json_headers['Authorization'] = r['token_type'] + ' ' + r['access_token']
		self.urlencoded_headers['Authorization'] = r['token_type'] + ' ' + r['access_token']
		self.refresh_token_thread = run(self.refresh_tokens, delay=int(r['expires_in']))

	def first_manual_startup(self):
		params = {
			"client_id": self.client_id,
			"redirect_uri": self.redirect_uri,
			"response_type": "code",
			"scope": "public+identify",
			"state": "randomval"
		}
		url = build_get_url('https://osu.ppy.sh/oauth/authorize', params) 
		if from_windows():
			import webbrowser
			webbrowser.open(url)
		else:
			# escape the '&' characters
			url = url.replace('&', '^&')
			os.system(f'cmd.exe /C "start {url}"')
		code = input('OsuAPI_v2: Enter the received code contained in the url after Authorizing:\n')
		params = {
			"client_id": self.client_id,
			"code": code,
			"grant_type": "authorization_code",
			"redirect_uri": self.redirect_uri
		}
		data = build_post_data(params)
		r = requests.request('POST', 'https://osu.ppy.sh/oauth/token', headers=self.urlencoded_headers, data=data)
		content = json.loads(r.content)
		if r.status_code != 200:
			report_request_error(r, content=content)
			exit()
		else:
			self.update_tokens(content)

	def refresh_tokens(self):
		print('OsuAPI_v2: refreshing token... ', end='')
		params = {
			"client_id": self.client_id,
			"client_secret": self.client_secret,
			"grant_type": "refresh_token",
			"refresh_token": self.refresh_token,
			"scope": "public+identify"
		}
		data = build_post_data(params)
		r = requests.request('POST', 'https://osu.ppy.sh/oauth/token', headers=self.token_headers, data=data)
		content = json.loads(r.content)
		error_msg = None
		if r.status_code != 200:
			if 'error_description' in content:
				if 'the refresh token is invalid' in content['error_description'].lower():
					with open('secrets/osu_api_v2_client_secret', 'w+') as f:
						f.write(input('OsuAPI_v2: The refresh token probably expired, reset your client secret and enter the new one:\n'))
					self.first_manual_startup()
				elif 'client authentication failed' in content['error_description'].lower():
					error_msg = 'OsuAPI_v2: Probably too many authentication requests were sent, retry again later'
				else:
					error_msg = 'OsuAPI_v2: Unknown error description'
			else:
				error_msg = 'OsuAPI_v2: Unknown error'
		if error_msg:
			cprint('failed', RED)
			print(error_msg)
			report_request_error(r, content=content)
			exit()
		else:
			self.update_tokens(content)
			cprint('done', GREEN)

	def __init__(self):
		# init constants
		self.client_id = '22868'
		with open('secrets/osu_api_v2_client_secret', 'r') as f:
			self.client_secret = f.read()
		self.redirect_uri = r'http%3A%2F%2Fdiscord%2Ecom'

		# get token
		if os.path.exists('secrets/osu_api_v2_refresh_token'):
			with open('secrets/osu_api_v2_refresh_token', 'r') as f:
				self.refresh_token = f.read()
			self.refresh_tokens()
		else:
			self.first_manual_startup()

	def user_info(self, username, mode):
		username_url = username.replace(' ', '%20')
		r = requests.request('GET', f'https://osu.ppy.sh/api/v2/users/{username_url}/{mode}', headers=self.json_headers)
		r_json = json.loads(r.content)
		return r_json if r.status_code == 200 else None

	def user_exists(self, username, mode):
		username_url = username.replace(' ', '%20')
		return requests.request('GET', f'https://osu.ppy.sh/api/v2/users/{username_url}/{mode}', headers=self.json_headers).status_code == 200

	def beatmap_info(self, beatmap_id):
		return json.loads(requests.request('GET', 'https://osu.ppy.sh/api/v2/beatmaps/'+str(beatmap_id), headers=self.json_headers).content)

	def user_recents(self, username, mode, limit):
		user_info = v2.user_info(username, 'osu')
		if not user_info: return []
		user_id = user_info['id']
		params = {
			"include_fails": "1",
			"mode": mode,
			"limit": limit
		}
		url = build_get_url(f'https://osu.ppy.sh/api/v2/users/{user_id}/scores/recent', params)
		return json.loads(requests.request('GET', url, headers=self.json_headers).content)

	def osu_file(self, beatmap_id):
		content = requests.request('GET', f'https://osu.ppy.sh/osu/{beatmap_id}').content
		return content.decode('utf-8') if type(content) is bytes else content

	def user_scores(self, username, beatmap_id):
		user_info = v2.user_info(username, 'osu')
		if not user_info: return []
		user_id = user_info['id']
		url = f'https://osu.ppy.sh/api/v2/beatmaps/{beatmap_id}/scores/users/{user_id}/all'
		return json.loads(requests.request('GET', url, headers=self.json_headers).content)

	def close(self):
		# if statement useless in theory
		if self.refresh_token_thread:
			self.refresh_token_thread.cancel()
		else:
			cprint('OsuAPI_v2: reached impossible statement?', RED)

# --------------------------------------------------------------------------- #

# call v1 or v2 as needed
class OsuAPI:

	user_scores_sort_by_aliases = {
		"accuracy": ['accuracy', 'acc'],
		"max_combo": ['max_combo', 'combo'],
		"passed": ['passed', 'pass', 'cleared', 'clear'],
		"pp": ['pp'],
		"rank": ['rank', 'note'],
		"score": ['score', 'points']
	}

	def __init__(self, save=False, save_dir=None):
		global v1, v2
		v1 = OsuAPI_v1()
		v2 = OsuAPI_v2()
		self.save = save
		self.save_dir = (save_dir if save_dir[-1] == '/' else save_dir+'/') if save_dir else 'api_v2_outputs/'

	def user_info(self, username, mode='osu'):
		raw = v2.user_info(username, mode)
		if not raw: return None
		r = extract_user_data(raw)
		if self.save:
			save_json(raw, self.save_dir+'user_info_raw.json')
			save_json(r, self.save_dir+'user_info.json')
		return r

	def user_exists(self, username):
		return v2.user_exists(username, 'osu')

	def user_recents(self, username, mode='osu', limit=5):
		r = v2.user_recents(username, mode if mode else v2.user_info(username, 'osu')['playmode'], limit)
		if self.save: save_json(r, self.save_dir+'user_recents.json')
		return r

	def user_recent(self, username, mode='osu'):
		r = self.user_recents(username, mode, 1)
		return [] if r == [] else r[0]

	def user_scores(self, username, beatmap_id, sort_by='pp'):
		r = v2.user_scores(username, beatmap_id)
		if self.save:
			save_json(r, self.save_dir+'user_scores_raw.json')
			save_json(r['scores'], self.save_dir+'user_scores.json')
		return [] if r['scores'] == [] else user_scores_sort_function(r['scores'], match_aliases(sort_by, self.user_scores_sort_by_aliases))

	def user_score(self, username, beatmap_id, sort_by='pp'):
		r = self.user_scores(username, beatmap_id, sort_by)
		return r if r == [] else r[0]

	def beatmap_info(self, beatmap_id):
		return v2.beatmap_info(beatmap_id)

	def osu_file(beatmap_id):
		return v2.osu_file(beatmap_id)

	def close(self):
		v1.close()
		v2.close()