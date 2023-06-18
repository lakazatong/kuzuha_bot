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

bot = None
osu_api = None

########################################### data ###########################################

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

########################################### osuset ###########################################

async def load_users():
	global users
	if os.path.exists(users_cache_path):
		with open(users_cache_path, 'r') as f:
			users = json.loads(f.read())

async def save_users():
	with open(users_cache_path, 'w+') as f: 
		f.write(json.dumps(users, indent=3))

async def osuset_cmd():
	user_info = osu_api.user_info(username)
	if user_info:
		users[str(ctx.message.author.id)] = username
		await ctx.send(f":white_check_mark: **{ctx.message.author}, your `Bancho` username has been edited to `{username}`**")
	else:
		await ctx.send(f'`{username}` **doesn\'t exist in the** `Bancho` **database.**')

########################################### osuset ###########################################

########################################### profile ###########################################

def build_profile_embed(ctx, profile_info, mode):
	try: # if ctx is actually a message object like for link detection
		server_user = ctx.message.author
	except:
		server_user = ctx.author
	# embed
	em = discord.Embed(description = '', colour = server_user.colour)
	username = profile_info['username']
	url_username = username.replace(' ', '%20')
	country_code = profile_info['country_code']
	em.set_author(	name = f"{gamemode_texts[mode]} Profile for {username}",
					icon_url = f'https://osu.ppy.sh/images/flags/{country_code}.png',
					url = f'https://osu.ppy.sh/users/{url_username}/{mode}')
	em.set_thumbnail(url = profile_info['avatar_url'])
	
	bancho_rank = profile_info['bancho_rank']
	peak_rank = profile_info['peak_rank']
	level = profile_info['level']
	level_progress = profile_info['level_progress']
	pp = profile_info['pp']
	acc = profile_info['acc']
	playcount = profile_info['playcount']
	playcount_hours = profile_info['playcount_hours']
	
	# info
	info = ""
	if bancho_rank != '-':
		countr_rank = profile_info['country_rank']
		info += f"▸ **Bancho Rank:** #{bancho_rank:,} ({country_code}#{countr_rank:,})\n"
	else:
		info += f"▸ **Bancho Rank:** {bancho_rank} ({country_code})\n"

	if profile_info['peak_rank'] != None:
		peak_rank_achieved = profile_info['peak_rank_achieved']
		info += f"▸ **Peak Rank:** #{peak_rank:,} achieved <t:{peak_rank_achieved}:R>\n"

	info += f"▸ **Level:** {level} + {level_progress:.2f}%\n"
	info += f"▸ **PP**: {pp:.2f} **Acc**: {round(acc, 2)}%\n"
	if playcount == 0:
		info += f"▸ **Playcount:** {playcount:,}\n"
	else:
		info += f"▸ **Playcount:** {playcount:,} ({playcount_hours:,} hrs)\n"
	if not profile_info['ranks_all_zero']:
		info += f"▸ **Ranks:** "
		for i, pair in enumerate(rank_emotes):
			rank_emote = pair[1]
			rank_count = profile_info['ranks'][i]
			info += f'{rank_emote}`{rank_count}`'
		info += "\n"
	em.description = info

	# footer
	linked = " | Verified" if profile_info['is_linked'] else ""
	if profile_info['is_online']:
		em.set_footer(text=f"On osu! Bancho Server{linked}", icon_url="https://i.imgur.com/DKLGecZ.png")
	else:
		last_seen = profile_info['last_seen']
		if last_seen:
			em.set_footer(text=f"Last Seen {last_seen} Ago on osu! Bancho{linked}", icon_url="https://i.imgur.com/sOtDO3u.png")
		else:
			em.set_footer(text=f"On osu! Bancho Server{linked}", icon_url="https://i.imgur.com/sOtDO3u.png")


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
		username = users.get(str(ctx.message.author.id))
		if username:
			await send_user_card(ctx, username, mode)
		else:
			await ctx.send('First use `~osuset <osu! pseudo>`')

########################################### profile ###########################################

########################################### recent ###########################################

recent_help_msg = code_to_txt(
f'''\
Usage:
	~recent|rs <username>
Description:
	Fetches <username> recent scores, filters, sorts and formats them.
Arguments:
	-p|pass|passed|clear|cleared	Filters out all failed scores.
	
	-m|mode 		<mode>			Filters out any other mode.
									<mode> aliases for:
										osu: std, standard, 0
										taiko: drum, drums, 1
										fruits: ctb, catch, 2
										mania: piano, tiles, 3
	
	-l|list 						List results.
	
	-b|best 						Sort recent scores with pp.
	
	-i|index 		<index>			Get score <index> from
									filtered and sorted results
									or start listing at <index>. (1-100)
	
	-?|search|find 	<map name>		Sort recent scores with
									similarity between <map name>
									and recent score's title.
									Overwrites -best sorting.\
'''
)

def user_score_embed_txts(user_score, mode):
	top_txt = f'**Recent {gamemode_texts[mode]} Play for {user_score['user']['username']}:**'
	beatmap_info = osu_api.beatmap_info(user_score['beatmap']['id'])
	stats = user_score['statistics']
	score_stats = score_stats(user_score, beatmap_info['id'])
	pp_value, acc_value, max_combo = score_stats['pp']['total'], score_stats['acc'], score_stats['max_combo']
	score_stats = score_stats(user_score, beatmap_info['id'], True, max_combo)
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
	map_txt = f'{beatmap_info['title']} [{beatmap_info['version']}] +{mods_text} [{beatmap_info['difficulty_rating']:.2f}★]'
	if rank == 'F':
		progress_value =(n300+n100+n50+nMiss)/\
						(beatmap_info['count_circles']+beatmap_info['count_sliders']+beatmap_info['count_spinners'])*100s
		pp_txt = f'▸ {rank_emotes[rank]} ({progress_value:.2f}%) ▸ **{pp_value:.2f}PP** ({pp_value_fc:.2f}pp for {acc_value_fc:.2f}% FC) ▸ {acc_value:.2f}%'
	else:
		pp_txt = f'▸ {rank_emotes[rank]} ▸ **{pp_value:.2f}PP** ({pp_value_fc:.2f}pp for {acc_value_fc:.2f}% FC) ▸ {acc_value:.2f}%'

	score_txt = f'▸ {user_score['score']:,} ▸ x{user_score['max_combo']}/{max_combo} ▸ {hits_txt}'
	try_count = 1
	for i in range(index+1, len(user_recents)):
		if user_recents[i]['beatmap']['id'] == beatmap_id: try_count += 1
		else: break
	
	replay_txt = ''
	if user_score['replay']:
		replay_txt = f' ▸ `[Replay](https://osu.ppy.sh/scores/taiko/{user_score['id']}/download`)'
	if user_score['created_at']:
		ago_value = convert_to_unix_time(user_score['created_at'], '%Y-%m-%dT%H:%M:%SZ')
		bottom_txt = f'Try #{try_count} ▸ <t:{ago_value}:R> ago{replay_txt}'
	else:
		bottom_txt = f'Try #{try_count}{replay_txt}'

	return top_txt, map_txt, pp_txt, score_txt, bottom_txt

def build_recents_embed(ctx, user_recents, mode, index):
	user_score = user_recents[index]
	beatmap_info, pp_text, pp_fc_text, acc_text, mods_text, stats = user_score_embed_txts(user_score, mode)
	rank = user_score['rank']
	beatmapset_id = beatmap_info['beatmapset_id']
	beatmap_id = beatmap_info['id']
	info = ''
	try_text = ''
	
	info += f'▸ {user_score['score']} ▸ x{user_score['max_combo']}/{beatmap_info['max_combo']} ▸ {hits_txt}'
	em = discord.Embed(description=info, colour=ctx.message.author.colour)
	em.set_author(
		name=, 
		url=f'https://osu.ppy.sh/beatmapsets/{beatmapset_id}#osu/{beatmap_id}',
		icon_url=user_info['avatar_url'])
	em.set_thumbnail(url=f'https://b.ppy.sh/thumb/{beatmapset_id}l.jpg')
		
	time_ago_text = format_time_ago(user_score['created_at'], )

	em.set_footer(text = f"{try_text}On osu! Bancho Server • {time_ago_text}", icon_url='https://i.imgur.com/Req9wGs.png')
	return embed

def build_recents_list_embed(ctx, user_recents, mode, passed):
	beatmap_info, F_rank, progress_text, pp_text, pp_fc_text, acc_text, mods_text = get_recents_embed_info(user_recents[index])
	beatmapset_id = beatmap_info['beatmapset_id']
	beatmap_id = beatmap_info['id']
	
	info = ""
	if F_rank:
		info += f'▸ {rank_emotes[rank]} ({progress_text:.1f}%) ▸ **{pp_text:.2f}** ({pp_text:.2f}) ▸ {acc_text:.2f}%\n'
	else:
		info += f'▸ {rank_emotes[rank]} ▸ **{pp_text:.2f}** ({pp_text:.2f}) ▸ {acc_text:.2f}%\n'

	em = discord.Embed(description=info, colour=ctx.message.author.colour)
	em.set_author(
		name=f'**Recent {gamemode_texts[mode]} Plays for {user_info['username']}:**', 
		url=f'https://osu.ppy.sh/beatmapsets/{beatmapset_id}#{beatmap_info['mode']}/{beatmap_id}',
		icon_url=user_info['avatar_url'])
	em.set_thumbnail(url=f'https://b.ppy.sh/thumb/{beatmapset_id}l.jpg')

	try_text = ''
	if F_rank:
		try_count = 1
		for i in range(index+1, len(user_recents)):
			if user_recents[i]['beatmap']['id'] == beatmap_id: try_count += 1
			else: break
		
	time_ago_text = format_time_ago(user_score['created_at'], '%Y-%m-%dT%H:%M:%SZ')

	em.set_footer(text = bottom_txt, icon_url='https://i.imgur.com/Req9wGs.png')

	embed_data = [
		{"title": "Page 1", "description": "This is the content of page 1."},
		{"title": "Page 2", "description": "This is the content of page 2."},
		{"title": "Page 3", "description": "This is the content of page 3."}
	]

	pages = []
	for data in embed_data:
		embed = discord.Embed(title=data["title"], description=data["description"])
		pages.append(embed)

	return pages

async def parse_recent_arguments(ctx):
	msg = ctx.message.content
	msg = msg.strip()
	while '  ' in msg:
		msg = msg.replace('  ', ' ')
	args = list(ctx.message.content.split(' '))
	
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
		if search_index+1 >= len(args): return False, _
		search = args[search_index+1]
		indexes.delete(search_index)
		indexes.delete(search_index+1)	

	# index
	index = None
	index_index = args.get('-i')
	if index_index == -1: index_index = args.get('-index')
	if index_index != -1:
		if index_index+1 >= len(args): return False, _
		index = args[index_index+1]
		try: index = int(index)
		except: return False, _
		if index < 1 or index > 100: return False, _
		index -= index # 1-100 -> 0-99
		indexes.delete(index_index)
		indexes.delete(index_index+1)

	# mode
	mode = None
	mode_index = args.get('-m')
	if mode_index == -1: mode_index = args.get('mode')
	if mode_index != -1:
		if mode_index+1 >= len(args): return False, _
		mode = match_aliases(args[mode_index+1], modes_aliases)
		if not mode: return False, _
		indexes.delete(mode_index)
		indexes.delete(mode_index+1)

	# everything left is considered as username
	usernames = [args[index] for index in indexes]

	return True, usernames, passed, mode, list_, best, index, search

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
	if user_recents == []: await ctx.send(f'**`{username}` has no recent plays in `Bancho` for `{gamemode_texts[mode]}`.**')
	msg = f'**Recent {gamemode_texts[mode]} Play for {user_recents[0]['user']['username']}:**'
	if not index: index = 0
	if index >= len(user_recents):
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
	# list
	if list_:
		# start listing at index
		pages = build_recents_list_embed(ctx, user_recents, mode, index)
		paginator = discord.ui.ButtonPaginator(pages)
		await paginator.start(ctx)
	else:
		# recent play index
		embed = build_recents_embed(ctx, user_recents, mode, index)
		await ctx.send(msg, embed=embed)

########################################### recent ###########################################

if __name__ == '__main__':
	bot = commands.Bot(command_prefix='~', intents=discord.Intents.all())
	bot.run(str(open('secrets/token', 'r').read()))

	osu_api = OsuAPI()