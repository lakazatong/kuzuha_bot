# invite url
'''
https://discord.com/api/oauth2/authorize?
	client_id=1103140474375647303&
	permissions=8&
	redirect_uri=https%3A%2F%2Fdiscord.com%2F&
	response_type=code&
	scope=applications.commands%20bot%20guilds%20guilds.members.read%20identify%20messages.read
'''

import discord
from discord.ext import commands
from libs.osu_api import *
try:
	import Levenshtein
except:
	os.system('pip install levenshtein')
	import Levenshtein

########################################### data ###########################################
discord_bot_token = open('secrets/discord_bot_token', 'r').read()
discord_headers = {
	"Authorization": "Bot "+discord_bot_token
	# "User-Agent": "DiscordBot (https://discord.com/api, 10)"
}

users = {}
users_cache_path = 'users.json'

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

########################################### data ###########################################


########################################### functions ###########################################

import discord

def dict_to_embed(embed_dict):
	embed = discord.Embed(
		type=embed_dict.get('type', 'rich'),
		title=embed_dict.get('title', None),
		description=embed_dict.get('description', None),
		color=embed_dict.get('color', discord.Color.default().value),
		timestamp=embed_dict.get('timestamp', None),
		url=embed_dict.get('url', None)
	)
	
	fields = embed_dict.get('fields', [])
	for field in fields:
		name = field.get('name', '')
		value = field.get('value', '')
		inline = field.get('inline', False)
		embed.add_field(name=name, value=value, inline=inline)
	
	image = embed_dict.get('image', {})
	embed.set_image(url=image.get('url', None))
	
	thumbnail = embed_dict.get('thumbnail', {})
	embed.set_thumbnail(url=thumbnail.get('url', None))
	
	author = embed_dict.get('author', {})
	embed.set_author(
		name=author.get('name', None),
		url=author.get('url', None),
		icon_url=author.get('icon_url', None)
	)
	
	footer = embed_dict.get('footer', {})	
	embed.set_footer(
		text=footer.get('text', None),
		icon_url=footer.get('icon_url', None)
	)

	return embed

def load_raw_message(path):
	raw = ''
	with open(path, 'r') as f:
		raw = f.read()
	raw = raw.replace('`', '"')
	raw = raw.replace('<', '&lt;')
	raw = raw.replace('>', '&gt;')
	# raw = raw.replace('true', 'True')
	# raw = raw.replace('false', 'False')
	# raw = raw.replace('null', 'None')
	lines = raw.split('\n')
	lines.pop(1)
	r = str(''.join(lines))
	for i in r.finds('"color"'):
		j = r[i+8:].find(',')+i+8
		if j == -1: j = r[i+8:].find('}')
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

def create_message(message, channel_id):
	...
	# headers = copy.copy(discord_headers)
	# headers['Content-Type'] = 'application/json'
	# print_json(message)
	# print_json(headers)
	# r = requests.request('POST', f'https://discord.com/api/v10/channels/{channel_id}/messages', data=message, headers=headers)
	# print_response(r)

########################################### functions ###########################################


########################################### osuset ###########################################

async def load_users():
	global users
	if os.path.exists(users_cache_path):
		try:
			users = load_json(users_cache_path)
		except:
			cprint('load_users: failed to load '+users_cache_path, RED)
	else:
		cprint(f'load_users: {users_cache_path} doesn\'t exists', RED)

async def save_users():
	try:
		save_json(users, users_cache_path)
	except:
		cprint('save_users: failed to save '+users_cache_path, RED)

def get_users():
	return users

def get_username(discord_user_id):
	return users.get(str(discord_user_id))

async def osuset_cmd(ctx, username):
	user_info = osu_api.user_info(username)
	if user_info:
		users[str(ctx.message.author.id)] = username
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
		username = get_username(ctx.message.author.id)
		if username:
			await send_user_card(ctx, username, mode)
		else:
			await ctx.send('First use `~osuset <osu! pseudo>`')

########################################### profile ###########################################

########################################### recent ###########################################

recent_help_msg = '''\
Usage:
	~recent|rs <username>
Description:
	Fetches <username> recent scores, filters, sorts and formats them.
Arguments:
	-p|pass|passed|clear|cleared    Filters out all failed scores.

	-m|mode			<mode>			Filters out any other mode.
									<mode> aliases for:
										osu: std, standard, 0
										taiko: drum, drums, 1
										fruits: ctb, catch, 2
										mania: piano, tiles, 3
	
	-l|list							List results.
	
	-b|best							Sort recent scores with pp.
	
	-i|index		<index>			Get score <index> from
									filtered and sorted results
									or start listing at <index>. (1-100)
	
	-?|search|find	<map name>		Sort recent scores with
									similarity between <map name>
									and recent score's title.
									Overwrites -best sorting.\
'''
# recent_help_embed = discord.Embed(description=recent_help_msg, colour = 1752220)

async def parse_recent_arguments(ctx):
	msg = ctx.message.content
	msg = msg.strip()
	while '  ' in msg:
		msg = msg.replace('  ', ' ')
	args = list(ctx.message.content.split(' '))
	err = False, [], None
	
	# start at 1 to ignore '~rs' or '~recent'
	indexes = list(range(1, len(args)))

	# list_
	list_ = False
	list_index = args.get('-l')
	if list_index == -1: list_index = args.get('-list')
	if list_index != -1:
		list_ = True
		indexes.delete(list_index)

	# best
	best = False
	best_index = args.get('-b')
	if best_index == -1: best_index = args.get('-best')
	if best_index != -1:
		best = True
		indexes.delete(best_index)

	# passed
	passed = False
	passed_index = args.get('-p')
	if passed_index == -1: passed_index = args.get('-pass')
	if passed_index == -1: passed_index = args.get('-passed')
	if passed_index == -1: passed_index = args.get('-clear')
	if passed_index == -1: passed_index = args.get('-cleared')
	if passed_index != -1:
		passed = True
		indexes.delete(passed_index)

	# search
	search = None
	search_index = args.get('-?')
	if search_index == -1: search_index = args.get('-search')
	if search_index == -1: search_index = args.get('-find')
	if search_index != -1:
		if search_index+1 >= len(args): return err
		search = args[search_index+1]
		indexes.delete(search_index)
		indexes.delete(search_index+1)	

	# index
	index = None
	index_index = args.get('-i')
	if index_index == -1: index_index = args.get('-index')
	if index_index != -1:
		if index_index+1 >= len(args): return err
		index = args[index_index+1]
		try: index = int(index)
		except: return err
		if index < 1 or index > 100: return err
		index -= index # 1-100 -> 0-99
		indexes.delete(index_index)
		indexes.delete(index_index+1)

	# mode
	mode = None
	mode_index = args.get('-m')
	if mode_index == -1: mode_index = args.get('mode')
	if mode_index != -1:
		if mode_index+1 >= len(args): return err
		mode = match_aliases(args[mode_index+1], modes_aliases)
		if not mode: return err
		indexes.delete(mode_index)
		indexes.delete(mode_index+1)

	# everything left is considered as username
	usernames = [args[index] for index in indexes]

	return True, usernames, (passed, mode, list_, best, index, search)

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

async def send_user_recent_card(ctx, username, passed, mode, list_, best, index, search):
	# username
	user_info = osu_api.user_info(username)
	if not user_info:
		await ctx.send(f':red_circle: **`{username}` not found.**')
		return
	# mode
	if not mode: mode = user_info['playmode']
	# index
	user_recents = osu_api.user_recents(username, mode, 100)
	if user_recents == []:
		await ctx.send(f'**`{username}` has no recent plays in `Bancho` for `{gamemode_texts[mode]}`.**')
		return
	if index and index >= len(user_recents):
		# checking now is not a problem since len(user_recents) can only go down (with passed)
		await ctx.send(f'**`{username}` has not enough recent plays in `Bancho` for `{gamemode_texts[mode]}` (`{len(user_recents)}` recent plays)**')
		return
	# passed
	if passed:
		i = 0
		while i < len(user_recents):
			if user_recents[i]['passed']: i += 1
			else: user_recents.pop(i)
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
			

########################################### recent ###########################################


########################################### bot ###########################################

bot = commands.Bot(command_prefix='~', intents=discord.Intents.all())

# allows to send menu like embeds (should be builtin tbh)
# source : https://github.com/AznStevy/owo-bot/blob/f7651f3cb7d67ba4d93e8ffa96d7a1d3120b2bd8/main.py#L306
async def menu(self, ctx, embed_list, files=[], message:discord.Message=None, page=0, timeout: int=30):
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

bot.menu = menu

########################################### bot ###########################################

osu_api = OsuAPI()
