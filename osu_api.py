import sys
sys.path.append('SessionSim/libs')
from classes import *

def card_cmd_function(session_sim, i, before=True):
	# i is the ith request in the har file (the first is the 0th)
	# runs before the request is sent
	if before:
		match i:
			case 0:
				session_sim.prepared_request['url'] = 'https://osu.ppy.sh/users/'+session_sim.mem['username'].replace(' ', '%20')+'/'+session_sim.mem['mode']
			case 1:
				# session_sim.previous_response.headers = {key.lower():value for key, value in session_sim.previous_response.headers.items()}
				session_sim.prepared_request['url'] = session_sim.previous_response.headers['Location']
				# session_sim.prepared_request['url'] = 'https://osu.ppy.sh/users/'+session_sim.mem['username'].replace(' ', '%20')+'/'+session_sim.mem['mode']
			case _:
				pass
	# runs after the request is sent
	else:
		match i:
			case _:
				pass

class OsuAPI:

	def __init__(self, debug_mode=False):
		self.session = SessionSim(debug_mode=debug_mode)
		self.session.cookie_manager.load_cookies_keys('cookies_keys.json')

	def _get_user_info(self):
		self.session.sim(1)
		sel = None
		with open(self.session.saved_response_content_path, 'r') as f: sel = Selector(f.read())
		r = json.loads(sel.xpath('/html/body/div[8]/div/@data-initial-data').get())
		# save_json(r, 'info_raw.json')
		user = r['user']
		ssh_count = user['statistics']['grade_counts']['ssh']
		ss_count = user['statistics']['grade_counts']['ss']
		sh_count = user['statistics']['grade_counts']['sh']
		s_count = user['statistics']['grade_counts']['s']
		a_count = user['statistics']['grade_counts']['a']
		info = {
			"username": self.session.mem['username'],
			"playmode": user['playmode'],
			"current_mode": r['current_mode'],
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
		return True, info

	def get_user_info(self, username, mode='osu'):
		print(f'getting user info of {username}... ')
		if not self.exists(username, mode): return False, None
		user_found, user_info = self._get_user_info()
		return user_found, user_info

	def exists(self, username, mode='osu'):
		self.session.critical_function = card_cmd_function
		self.session.mem['username'] = username
		self.session.mem['mode'] = mode
		self.session.load_har('user_info.har')
		self.session.sim(0)
		user_found = True
		with open(self.session.saved_response_content_path, 'r') as f:
			user_found = f.read().find('User not found! ;_;') == -1
		return user_found

	def close(self):
		self.session.cookie_manager.save_cookies_keys('cookies_keys.json')