# invite url
'''
https://discord.com/api/oauth2/authorize?
	client_id=1103140474375647303&
	permissions=8&
	redirect_uri=https%3A%2F%2Fdiscord.com%2F&
	response_type=code&
	scope=applications.commands%20bot%20guilds%20guilds.members.read%20identify%20messages.read
'''

import math
from libs.osu_api import *
from libs.perf import *
try:
	import discord
except:
	os.system('pip install discord')
	import discord
from discord.ext import commands
try:
	import Levenshtein
except:
	os.system('pip install levenshtein')
	import Levenshtein

########################################### data ###########################################

discord_bot_token = ''
with open('secrets/discord_bot_token', 'r') as f:
	discord_bot_token = f.read()
discord_headers = {
	"Authorization": "Bot "+discord_bot_token
	# "User-Agent": "DiscordBot (https://discord.com/api, 10)"
}

# cache
users = {}

gamemode_texts = {
	"osu": 'osu! Standard',
	"taiko": 'Taiko',
	"fruits": 'Catch The Beat!',
	"mania": 'osu! Mania'
}

modes_aliases = {
	'osu': ['osu', 'std', 'standard', '0'],
	'taiko': ['taiko', 'drum', 'drums', '1'],
	'fruits': ['fruits', 'ctb', 'catch', '2'],
	'mania': ['mania', 'piano', 'tiles', '3']
}

rank_emotes = {
	"XH":"<:EmoteName:1119272076730175558>",
	"X": "<:EmoteName:1119272089971605504>",
	"SH":"<:EmoteName:1119272112138506331>",
	"S": "<:EmoteName:1119272128055881739>",
	"A": "<:EmoteName:1119272145567092756>",
	"B": "<:EmoteName:1119272157965463573>",
	"C": "<:EmoteName:1119272169424310384>",
	"D": "<:EmoteName:1119272235945963590>",
	"F": "<:EmoteName:1119272252337295420>"
}

scores_filters = {
	"passed": ['pass', 'cleared', 'clear'],
	"replay": [],
	"pin": ['pinned']
}

scores_sorts = {
	"accuracy": ['acc'],
	"max_combo": ['combo'],
	"pp": [],
	"rank": ['note'],
	"score": ['points']
}

ACTIVE_BUTTON = discord.ui.Button(
	style=discord.ButtonStyle.secondary,
	custom_id='active_button',
	disabled=True,
	label='Active'
)

running_tasks = set()
RUNNING = True

########################################### data ###########################################


########################################### functions ###########################################

async def load_users():
	global users
	if os.path.exists('cache/users.json'):
		try:
			users = load_json('cache/users.json')
		except:
			cprint('load_users: failed to load '+'cache/users.json', RED)
	else:
		cprint(f'load_users: cache/users.json doesn\'t exists', RED)

async def save_users():
	try:
		save_json(users, 'cache/users.json')
	except:
		cprint('save_users: failed to save cache/users.json', RED)

async def close():
	global osu_api, RUNNING, running_tasks
	osu_api.close()
	RUNNING = False
	while any(not task.done() for task in running_tasks): await asyncio.sleep(1)
	await save_users()

async def is_author(interaction):
	return interaction.user.id == ctx.author.id

def load_raw(path):
	# file at path contains a dict returned by auto code embed generator
	raw = ''
	with open(path, 'r') as f:
		raw = str(f.read())
	tmp = raw.finds('`')
	for i in tmp:
		if raw[i-1] != '\\':
			raw = raw[:i]+'"'+raw[i+1:]
	raw = raw.replace('\\`', '`')
	lines = raw.split('\n')
	lines.pop(1)
	r = str('\n'.join(lines))
	for i in r.finds('"color"'):
		j = r[i+8:].find(',')
		if j == -1: j = min(r[i+8:].find('\n'), r[i+8:].find('}'))
		j += i+8
		if j != -1:
			color = r[i+8:j].strip()
			r = r[:i+8]+f' {int(color[2:], 16)}'+r[j:]
		else:
			cprint('wtf', RED)
	try:
		json.loads(r)
	except json.decoder.JSONDecodeError as e:
		print(e)
		e = str(e.__repr__())
		i = e.finds('(')[1]
		i = int(e[i+6:-3])
		print(r[i-i%50:i+50-i%50])
		print(r[i-1:i+1])
		exit()
	return r

def create_message(message, channel_id=None, channel=None):
	if not channel_id and not channel:
		cprint('create_message: need at least channel_id', 'red')
		return
	# message as a dict returned by auto code embed generator
	if type(message) is dict:
		try:
			message = json.dumps(message)
		except Exception as e:
			cprint(f'create_message: failed to json.dumps(message) ({e})', 'red')
			return
	discord_headers['Content-Type'] = 'application/json'
	try:
		if not channel_id: channel_id = channel.id
		r = requests.request('POST', f'https://discord.com/api/v10/channels/{channel_id}/messages', data=message, headers=discord_headers)
	except Exception as e:
		cprint(f'create_message: failed to make POST request ({e})', 'red')
		return None
	data = None
	try:
		data = json.loads(r.content)
	except Exception as e:
		cprint(f'create_message: failed to json.loads(r.content)[\'id\'] ({e})', 'red')
		print_response(r)
		return None
	try:
		r = discord.Message(state=bot._connection, channel=channel if channel else bot.get_channel(channel_id), data=data)
	except Exception as e:
		cprint(f'create_message: failed to create discord.Message from response ({e})', 'red')
		print_response(r)
		return None
	return r

def sort_scores(scores, key):
	key = match_aliases(scores_sorts, key)
	r = sorted(scores, key=lambda x: x[key])
	if key == 'rank':
		while not r[0]['rank'] in ['SSH', 'SS', 'SH', 'S']: r.append(r.pop(0))
	else:
		r.reverse()
	return r

def filter_scores(scores, key):
	key = match_aliases(scores_filters, key)
	if key == 'passed' or key == 'replay':
		i = 0
		while i < len(scores):
			if scores[i][key]: i += 1
			else: scores.pop(i)
	elif key == 'pin':
		i = 0
		while i < len(scores):
			if scores[i]['current_user_attributes'][key]['is_pinned']: i += 1
			else: scores.pop(i)
	else:
		cprint(f'filter_scores: Unknown key ({key}')
	return r

def argument_is_mods(arg):
	mods = []
	if len(arg) < 3 or len(arg)%2 == 0: return False, None
	if arg[0] != '+': return False, None
	if arg[1] == 'N' and arg[2] == 'M': return True, ['NM']
	for i in range(1, len(arg), 2):
		cut = arg[i]+arg[i+1]
		for mod in ['NF', 'SD', 'PF', 'EZ', 'HR', 'HD', 'DT', 'NC', 'HT', 'FL', 'SO', 'FI', 'MR']:
			if cut == mod:
				mods.append(mod)
				break
	return True, mods

# allows to send menu like embeds (should be builtin tbh)
# source : https://github.com/AznStevy/owo-bot/blob/f7651f3cb7d67ba4d93e8ffa96d7a1d3120b2bd8/main.py#L306
async def score_menu(self, ctx, embed_list, files=[], message:discord.Message=None, page=0, timeout: int=30):
	def react_check(r, u):
		return u == ctx.author and r.message.id == message.id and str(r.emoji) in expected

	expected = ["➡", "⬅"]
	numbs = {
		"end": ":track_next:",
		"next": "➡",
		"back": "⬅",
		"first": ":track_previous:",
		"exit": "❌"
	}

	embed = embed_list[page]

	if not message:
		message = await ctx.send(embed=embed, files=files)
		if len(embed_list) > 1:
			await message.add_reaction("⬅")
			await message.add_reaction("➡")
	else:
		await message.edit(embed=embed, files=files)

	try:
		react = await self.wait_for('reaction_add', check=react_check, timeout=timeout)
	except asyncio.TimeoutError:
		try:
			await message.clear_reactions()
		except discord.Forbidden:  # cannot remove all reactions
			for emote in expected:
				await message.remove_reaction(emote, self.user)
		return None

	if react is None:
		try:
			try:
				await message.clear_reactions()
			except:
				await message.remove_reaction("⬅", self.user)
				await message.remove_reaction("➡", self.user)
		except:
			pass
		return None
	reacts = {v: k for k, v in numbs.items()}
	react = reacts[react[0].emoji]
	if react == "next":
		page += 1
		next_page = page % len(embed_list)
		try:
			await message.remove_reaction("➡", ctx.message.author)
		except:
			pass
		return await self.menu(ctx, embed_list, message=message, page=next_page, timeout=timeout)
	elif react == "back":
		page -= 1
		next_page = page % len(embed_list)
		try:
			await message.remove_reaction("⬅", ctx.message.author)
		except:
			pass
		return await self.menu(ctx, embed_list, message=message, page=next_page, timeout=timeout)

def get_discord_user_info(user_id):
	r = requests.request('GET', f'https://discord.com/api/v10/users/{user_id}', headers=discord_headers)
	return json.loads(r.content)

def get_discord_channel_message_info(channel_id, message_id):
	r = requests.request('GET', f'https://discord.com/api/v10/channels/{channel_id}/messages/{message_id}', headers=discord_headers)
	return json.loads(r.content)

def get_member(member_id):
	return discord.utils.find(lambda m: m.id == member_id, bot.get_all_members())

########################################### functions ###########################################


########################################### osuset ###########################################

def get_users():
	return users

def get_user_info(discord_user_id):
	return users.get(str(discord_user_id))

async def osuset_cmd(ctx, username):
	user_info = osu_api.user_info(username)
	if user_info:
		discord_user_id = str(ctx.message.author.id)
		if discord_user_id in users:
			users[discord_user_id]['osu']['username'] = username
		else:
			users[discord_user_id] = {
				"osu": {
					"username": username,
					"avatar_hash": None
				},
				"discord": {
					"avatar_hash": None,
					"display_avatar_hash": None
				}
			}
		await ctx.send(f":white_check_mark: **{ctx.message.author}, your `Bancho` username has been edited to `{username}`**")
	else:
		await ctx.send(f'`{username}` **doesn\'t exist in the** `Bancho` **database.**')

########################################### osuset ###########################################

########################################### profile ###########################################

def build_profile_embed(ctx, user_info, mode):
	try: # if ctx is actually a message object like for link detection
		server_user = ctx.message.author
	except:
		server_user = ctx.author
	# embed
	em = discord.Embed(description = '', colour = server_user.colour)
	username = user_info['username']
	username_url = username.replace(' ', '%20')
	country_code = user_info['country_code']
	em.set_author(	name = f"{gamemode_texts[mode]} Profile for {username}",
					icon_url = f'https://osu.ppy.sh/images/flags/{country_code}.png',
					url = f'https://osu.ppy.sh/users/{username_url}/{mode}')
	em.set_thumbnail(url = user_info['avatar_url'])
	
	bancho_rank = user_info['bancho_rank']
	peak_rank = user_info['peak_rank']
	level = user_info['level']
	level_progress = user_info['level_progress']
	pp = user_info['pp']
	acc = user_info['acc']
	playcount = user_info['playcount']
	playcount_hours = user_info['playcount_hours']
	
	# info
	info = ""
	if bancho_rank != '-':
		countr_rank = user_info['country_rank']
		info += f"▸ **Bancho Rank:** #{bancho_rank:,} ({country_code}#{countr_rank:,})\n"
	else:
		info += f"▸ **Bancho Rank:** {bancho_rank} ({country_code})\n"

	if user_info['peak_rank'] != None:
		peak_rank_achieved = user_info['peak_rank_achieved']
		info += f"▸ **Peak Rank:** #{peak_rank:,} achieved <t:{peak_rank_achieved}:R>\n"

	info += f"▸ **Level:** {level} + {level_progress:.2f}%\n"
	info += f"▸ **PP**: {pp:.2f} **Acc**: {round(acc, 2)}%\n"
	if playcount == 0:
		info += f"▸ **Playcount:** {playcount:,}\n"
	else:
		info += f"▸ **Playcount:** {playcount:,} ({playcount_hours:,} hrs)\n"
	if not user_info['ranks_all_zero']:
		info += f"▸ **Ranks:** "
		for i, (key, value) in enumerate(rank_emotes.items()):
			if i > 4: break
			rank_count = user_info['ranks'][i]
			info += f'{value}`{rank_count}`'
		info += "\n"
	em.description = info

	# footer
	verified = " | Verified" if user_info['is_verified'] else ""
	if user_info['is_online']:
		em.set_footer(text=f"On osu! Bancho Server{verified}", icon_url="https://i.imgur.com/DKLGecZ.png")
	else:
		last_seen = user_info['last_seen']
		if last_seen:
			em.set_footer(text=f"Last Seen {last_seen} Ago on osu! Bancho{verified}", icon_url="https://i.imgur.com/sOtDO3u.png")
		else:
			em.set_footer(text=f"On osu! Bancho Server{verified}", icon_url="https://i.imgur.com/sOtDO3u.png")


	return em

async def send_user_card(ctx, username, mode):
	user_info = osu_api.user_info(username, mode=mode)
	if user_info:
		embed = build_profile_embed(ctx, user_info, mode)
		await ctx.send(embed=embed)
	else:
		await ctx.send(f':red_circle: **`{username}` not found.**')

async def card_cmd(ctx, username, mode):
	if username:
		await send_user_card(ctx, username, mode)
	else:
		user_info = get_user_info(ctx.message.author.id)
		if user_info:
			await send_user_card(ctx, user_info['osu']['username'], mode)
		else:
			await ctx.send('First use `~osuset <osu! pseudo>`')

########################################### profile ###########################################

########################################### recent ###########################################
recent_help_msg = '''\
Usage:
	~recent|rs <username>
Description:
	Fetches 100 of <username> recent scores.
	If no username is provided, it will use the user's osu! profile set with ~osuset.
Options:
	Filters:
		-m|mode			<mode>			Filters out all other mode.
										<mode> options:
											osu 	(std, standard, 0)
											taiko 	(drum, drums, 1)
											fruits 	(ctb, catch, 2)
											mania 	(piano, tiles, 3)
		
		+<mods>							Filters out any score that
										lack at least one of the mods.
										Scores with the most mods will show up first.
										<mods> options:
											NF, SD, PF, EZ, HR, HD, DT,
											NC, HT, FL, SO, FI, MR

		-p|pass|passed|clear|cleared    Filters out failed scores.
	Sorts:
		-s|sort			<sort>			Sorts recent scores.
										<sort> options:
											pp
											score
											rank
											accuracy (acc)
											max_combo (combo)

		-?|search|find	<map name>		Sorts recent scores by
										similarity between <map name>
										and recent scores titles.
										Overwrites any other sorting.
	Formating:
		-l|list							Lists results, 5 scores per page.

		-i|index		<index>			Gets score <index> from
										filtered and sorted results
										or start listing at <index>. (1-100)

		default							Equivalent to -i 1.
'''
# recent_help_embed = discord.Embed(description=recent_help_msg, colour = 1752220)

def user_recent_embed_txts(user_recent, mode):
	beatmap_info = osu_api.beatmap_info(user_recent['beatmap']['id'])
	stats = user_recent['statistics']
	score_stats = get_score_stats(user_recent, beatmap_info['id'])
	pp_value, acc_value, max_combo = score_stats['pp']['total'], score_stats['acc'], score_stats['max_combo']
	score_stats = score_stats(user_recent, beatmap_info['id'], True, max_combo)
	pp_value_fc, acc_value_fc = score_stats['pp']['total'], score_stats['acc']
	mods_text = ''.join(beatmap_info['mods'])
	if mods_text == '': mods_text = 'No Mod'
	n300, n100, n50, nMiss = stats['count_300'], stats['count_100'], stats['count_50'], stats['count_miss']
	nGeki, nKatu = stats['count_geki'], stats['count_katu']
	match mode:
		case 'osu' | 'fruits':
			hits_txt = f'[{n300}/{n100}/{n50}/{nMiss}]'
		case 'taiko':
			hits_txt = f'[{n300}/{n100}/{nMiss}]'
		case 'mania':
			hits_txt = f'[{nGeki}/{n300}/{nKatu}/{n100}/{n50}/{nMiss}]'
	beatmap_title = beatmap_info['title']
	beatmap_version = beatmap_info['version']
	beatmap_sr = beatmap_info['difficulty_rating']

	beatmapset_id = beatmap_info['beatmapset_id']
	beatmap_id = beatmap_info['id']
	beatmap_url = f'https://osu.ppy.sh/beatmapsets/{beatmapset_id}#{mode}/{beatmap_id}'
	map_txt = f'[{beatmap_title} [{beatmap_version}]]({beatmap_url}) +**{mods_text}** [{beatmap_sr:.2f}★]'
	rank_emote = rank_emotes[rank]
	if rank == 'F':
		progress_value =(n300+n100+n50+nMiss)/\
						(beatmap_info['count_circles']+beatmap_info['count_sliders']+beatmap_info['count_spinners'])*100
		
		pp_txt = f'▸ {rank_emote} ({progress_value:.2f}%) ▸ **{pp_value:.2f}PP** ({pp_value_fc:.2f}pp for {acc_value_fc:.2f}% FC) ▸ {acc_value:.2f}%'
	else:
		pp_txt = f'▸ {rank_emote} ▸ **{pp_value:.2f}PP** ({pp_value_fc:.2f}pp for {acc_value_fc:.2f}% FC) ▸ {acc_value:.2f}%'

	user_recent_score = user_recent['score']
	user_recent_max_combo = user_recent['max_combo']
	score_txt = f'▸ {user_recent_score:,} ▸ x{user_recent_max_combo}/{max_combo} ▸ {hits_txt}'
	try_count = 1
	for i in range(len(user_recents)):
		if user_recents[i]['beatmap']['id'] == beatmap_id: try_count += 1
		else: break
	
	replay_txt = ''
	if user_recent['replay']:
		score_id = user_recent['id']
		replay_txt = f' ▸ `[Replay](https://osu.ppy.sh/scores/taiko/{score_id}/download`)'
	if user_recent['created_at']:
		ago_value = convert_to_unix_time(user_recent['created_at'], '%Y-%m-%dT%H:%M:%SZ')
		bottom_txt = f'Try #{try_count} ▸ <t:{ago_value}:R> ago{replay_txt}'
	else:
		bottom_txt = f'Try #{try_count}{replay_txt}'

	return map_txt, pp_txt, score_txt, bottom_txt, beatmap_info

def build_recents_embed(ctx, user_info, user_recents, mode):
	try: # if ctx is actually a message object like for link detection
		server_user = ctx.message.author
	except:
		server_user = ctx.author
	pages = []
	username = user_info['username']
	username_url = username.replace(' ', '%20')
	country_code = user_info['country_code'].lower()
	top_txt = f':flag_{country_code}: **Recent {gamemode_texts[mode]} Plays for {username}:**'
	for user_recent in user_recents:
		map_txt, pp_txt, score_txt, bottom_txt, beatmap_info = user_recent_embed_txts(user_recent, mode)
		description = f'{pp_txt}\n{score_txt}'
		em = discord.Embed(description = description, colour = server_user.colour)
		em.set_author(	name = map_txt,
						icon_url = user_info['avatar_url'])
		beatmapset_id = beatmap_info['beatmapset_id']
		em.set_thumbnail(url = f'https://b.ppy.sh/thumb/{beatmapset_id}l.jpg')
		em.set_footer(text=bottom_txt, icon_url=osu_api.logo_url)
		pages.append(em)
	return top_txt, pages

def build_recents_list_embed(ctx, user_info, user_recents, mode):
	try: # if ctx is actually a message object like for link detection
		server_user = ctx.message.author
	except:
		server_user = ctx.author
	pages = []
	username = user_info['username']
	username_url = username.replace(' ', '%20')
	country_code = user_info['country_code'].lower()
	top_txt = f'**:flag_{country_code}: Recent {gamemode_texts[mode]} Plays for {username}:**'
	nb_pages = ceil(len(user_recents)/5)
	page = 1
	for i in range(0, len(user_recents), 5):
		map_txt, pp_txt, score_txt, bottom_txt, _ = user_recent_embed_txts(user_recents[i], mode)
		description = f'**{i+1})** {map_txt}\n{pp_txt}\n{score_txt}\n{bottom_txt}'
		map_txt, pp_txt, score_txt, bottom_txt, _ = user_recent_embed_txts(user_recents[i+1], mode)
		description += f'**{i+2})** {map_txt}\n{pp_txt}\n{score_txt}\n{bottom_txt}'
		map_txt, pp_txt, score_txt, bottom_txt, _ = user_recent_embed_txts(user_recents[i+2], mode)
		description += f'**{i+3})** {map_txt}\n{pp_txt}\n{score_txt}\n{bottom_txt}'
		map_txt, pp_txt, score_txt, bottom_txt, _ = user_recent_embed_txts(user_recents[i+3], mode)
		description += f'**{i+4})** {map_txt}\n{pp_txt}\n{score_txt}\n{bottom_txt}'
		map_txt, pp_txt, score_txt, bottom_txt, _ = user_recent_embed_txts(user_recents[i+4], mode)
		description += f'**{i+5})** {map_txt}\n{pp_txt}\n{score_txt}\n{bottom_txt}'
		em = discord.Embed(description = description, colour = server_user.colour)
		em.set_thumbnail(url = user_info['avatar_url'])
		em.set_footer(text=f'On osu! `Bancho` Server | Page {page} of {nb_pages}', icon_url=osu_api.logo_url)
		page += 1
		pages.append(em)
	return top_txt, pages

async def send_user_recent_card(ctx, username, mode, passed, list_, best, index, search):
	# username
	user_info = osu_api.user_info(username)
	if not user_info:
		await ctx.send(f':red_circle: **`{username}` not found.**')
		return
	# mode
	if not mode: mode = user_info['playmode']
	# best
	user_recents = osu_api.user_recents(username, mode, 100)
	if user_recents == []:
		await ctx.send(f'**`{username}` has no recent plays in `Bancho` for `{gamemode_texts[mode]}`.**')
		return
	if index and index >= len(user_recents):
		# checking now is not a problem since len(user_recents) can only go down (with passed)
		await ctx.send(f'**`{username}` has not enough recent plays in `Bancho` for `{gamemode_texts[mode]}` (`{len(user_recents)}` recent plays)**')
		return
	
	# best
	if best:
		user_recents = sorted(user_recents, key=lambda x: x['pp'])
		user_recents.inverse() # because pp = None <=> pp = 0
	# search
	if search:
		search_lower = search.lower()
		user_recents = sorted(user_recents, key=lambda x: Levenshtein.distance(search_lower, x["title"].lower()) / max(len(search), len(x["title"])))
	# index
	page = 0
	if index:
		page = index//5 if list_ else index
		msg, pages = build_recents_embed(ctx, user_info, user_recents, mode)
	else:
		# list
		msg, pages = build_recents_list_embed(ctx, user_info, user_recents, mode) if list_ else build_recents_embed(ctx, user_info, user_recents, mode)
	await bot.menu(ctx, pages, page=page, message=msg)

recent_options = {
	# format:
	# "short": [takes_arg, longs]
	"h": [False, 'help'],
	"m": [True, 'mode'],
	"p": [False, 'pass', 'passed', 'clear', 'cleared'],
	"s": [True, 'sort'],
	"?": [True, 'search', 'find'],
	"l": [False, 'list'],
	"i": [True, 'index']
}

async def recent_cmd(ctx, arguments, options):
	if len(usernames) == 0:
		user_info = get_user_info(ctx.message.author.id)
		if user_info:
			await send_user_recent_card(ctx, user_info['osu']['username'], *options)
		else:
			await ctx.channel.send('First use `~osuset <osu! pseudo>`')
			return
	else:
		for username in usernames:
			await send_user_recent_card(ctx, username, *options)

########################################### recent ###########################################


########################################### ainsi ###########################################

def ansi_text_discord(text, esc_format, esc, end, black_bg):
	r = ansi_text(text, esc_format, esc, end)
	return (esc+'[40m'+r+esc+'[0m' if black_bg else r) if r else ''

ansi_options = {
	# format:
	# "short": [takes_arg, longs]
	"h": [False, 'help'],
	"f": [True, 'format', 'esc-format'],
	"_": [True, 'escape', 'esc'],
	"e": [True, 'end'],
	"b": [False, 'black_bg', 'black']
}

async def ansi_cmd(ctx, arguments, *options):
	timeout = False
	view = discord.ui.View(timeout=300)
	view.interaction_check = is_author
	async def on_timeout():
		nonlocal timeout
		timeout = True
	view.on_timeout = on_timeout
	view.add_item(ACTIVE_BUTTON)

	out = capture_console_output(ansi_text_discord, ' '.join(arguments), *options)
	msg = await ctx.channel.send('```ansi\n'+out+'```', view=view)
	wait = 0
	max_wait = 30
	last_edit_time = ctx.message.created_at
	while not timeout and RUNNING:
		await asyncio.sleep(1)
		print(f'ansi: waiting {ctx.message.author.name}... '+str(wait))
		wait += 1
		if wait == max_wait: break
		async for entry in ctx.channel.history(limit=1, before=msg):
			if not entry.edited_at or entry.edited_at == last_edit_time or (entry.edited_at - last_edit_time).total_seconds() >= max_wait:
				continue
			arguments, options = parse(entry.content, ansi_options)
			if options[0]:
				await msg.edit(content='ansi help msg')
				wait = 0
				last_edit_time = entry.edited_at
				break
			out = capture_console_output(ansi_text_discord, ' '.join(arguments), *options[1:])
			await msg.edit(content='```ansi\n'+out+'```')
			wait = 0
			last_edit_time = entry.edited_at
			break
	
	last_content = '```ansi\n'+out+'```'
	if timeout: last_content = 'time\'s up\n' + last_content
	await msg.edit(content=last_content, view=None)

########################################### ainsi ###########################################


########################################### avatar ###########################################

async def cache_member_avatar(member, avatar_hash, account, path, size, max_size):
	if size:
		member.avatar.with_size(size).save(path)
	else:
		
		base_url, _ = deconstruct_get_url(member.avatar.url)
		member.avatar.url = base_url + f'?size={max_size}'
		await member.avatar.save(path)
	if account:
		if member.id in users:
			users[str(member.id)]['discord']['display_avatar_hash'] = avatar_hash
		else:
			users[str(member.id)] = {
				"osu": {
					"username": None,
					"avatar_hash": None
				},
				"discord": {
					"avatar_hash": avatar_hash,
					"display_avatar_hash": None
				}
			}
	else:
		if member.id in users:
			users[str(member.id)]['discord']['avatar_hash'] = avatar_hash
		else:
			users[str(member.id)] = {
				"osu": {
					"username": None,
				},
				"discord": {
				}
			}

def get_avatar(member_id, avatar_hash, account, max_size):
	display_txt = '_display' if account else ''
	r = requests.request('GET', f'https://cdn.discordapp.com/avatars/{member_id}/{avatar_hash}.png?size={max_size}')
	if not r:
		cprint(f'dl_avatar: failed to download avatar {avatar_hash} from {member_id} (size {max_size})', 'red')
		print_response(r)
	return r

def dl_avatar(member_id, avatar_hash, account, max_size, path):
	with open(path, 'w+') as f:
		f.write(get_avatar(member_id, avatar_hash, max_size).content)

def extract_id(i, args, member):
	if args[i] == str(member.id): return args.pop(i)
	return None
def extract_username(i, args, member):
	if args[i] == member.name: return args.pop(i)
	return None

async def avatar_cmd_discord(args, account, size, max_size):
	avatars = {}
	extracts = []
	for i, arg in enumerate(args):
		if arg.isdigit():
			extracts.append(extract_id)
		elif arg.isalpha():
			extracts.append(extract_username)
		else:
			args[i] = arg[2:-1]
			extracts.append(extract_id)
	for member in bot.get_all_members():
		skip = True
		for i in range(len(args)):
			if extracts[i](i, args, member):
				extracts.pop(i)
				skip = False
		if skip: continue
		path = f'cache/discord/avatars/{member.id}'
		if not os.path.exists(path):
			os.mkdir(path)
		if member.avatar or member.display_avatar:
			avatar, display_avatar = str(member.avatar), str(member.display_avatar)
			max_size = ((2 ** max(4, max_size)) if max_size <= 12 else min(4096, 2 ** round(math.log2(max_size)))) if max_size else 4096
			size = max(16, min(4096, size)) if size else 4096
			if account:
				base_url, _ = deconstruct_get_url(avatar)
				base_url = base_url[len('https://cdn.discordapp.com/avatars/'):]
				avatar_hash = base_url[:base_url.find('.')].split('/')[1]
				dl_avatar(member.id, avatar_hash, max_size, f'{path}/{avatar_hash}.png')
			else:
				if 'guilds' in display_avatar:
					base_url, _ = deconstruct_get_url(avatar)
					base_url = str(base_url[len('https://cdn.discordapp.com/guilds/'):])
					tmp = base_url[base_url.finds('/')[-1]+1:]
					avatar_hash = tmp[:tmp.find('.')]
				else:
					base_url, _ = deconstruct_get_url(display_avatar)
					base_url = base_url[len('https://cdn.discordapp.com/avatars/'):]
					avatar_hash = base_url[:base_url.find('.')].split('/')[1]
				dl_avatar(member.id, avatar_hash, max_size, f'{path}/{avatar_hash}.png')
			
			if os.path.exists(path+f'/{size}'):
				...
		else:
			path += f'cache/discord/avatars/default/' + member.default_avatar[len('https://cdn.discordapp.com/embed/avatars/')]
		
		avatars[member.name] = path+'.png'
		if args == []: break
	
	return avatars


async def avatar_cmd_osu(user_ids, size, max_size):
	avatars = {}
	
	return avatars

avatar_options = {
	"h": [False, 'help'],
	"o": [False, 'osu'],
	"a": [False, 'account'],
	"s": [True, 'size'],
	"m": [True, 'max_size']
}

async def avatar_cmd(ctx, args, osu, account, size, max_size):
	if osu:
		avatars = await avatar_cmd_osu(args, size, max_size)
	else:
		avatars = await avatar_cmd_discord(args, account, size, max_size)
	content = 'Avatars of: '
	files = []
	for username, path in avatars.items():
		content += f'{username}, '
		files.append(discord.File(path))
	if len(files) == 1:
		await ctx.channel.send(content=content[:-2], file=files[0])
	else:
		await ctx.channel.send(content=content[:-2], files=files)

########################################### avatar ###########################################


bot = commands.Bot(command_prefix='~', intents=discord.Intents.all())
bot.score_menu = score_menu

osu_api = OsuAPI()