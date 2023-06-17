# invite url
'''
https://discord.com/api/oauth2/authorize?client_id=1103140474375647303&permissions=8&redirect_uri=https%3A%2F%2Fdiscord.com%2F&response_type=code&scope=applications.commands%20bot%20guilds%20guilds.members.read%20identify%20messages.read
'''

import discord
from discord.ext import commands
import sys
sys.path.append('libs')
from osu_api import *

users = {}
users_cache_path = 'users.json'

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='~', intents=intents)
osu_api = OsuAPI()

async def load_users():
	global users
	if os.path.exists(users_cache_path):
		with open(users_cache_path, 'r') as f:
			users = json.loads(f.read())

async def save_users():
	with open(users_cache_path, 'w+') as f: 
		f.write(json.dumps(users, indent=3))

@bot.event
async def on_ready():
	await load_users()
	print(f'Logged in as {bot.user.name} ({bot.user.id})')

@bot.command()
async def r(ctx):
	await ctx.message.delete()
	os.execv(sys.executable, ['python3'] + sys.argv)

@bot.command()
@commands.is_owner()
async def q(ctx):
	osu_api.close()
	await save_users()
	await ctx.bot.close()

@bot.command()
async def send_users(ctx):
	await ctx.send(json.dumps(users, indent=3))

@bot.command()
async def osuset(ctx, username=''):
	if username == '':
		await ctx.send('`Usage: ~osuset <osu! pseudo>`')
	else:
		user_info = osu_api.user_info(username)
		if user_info:
			users[str(ctx.message.author.id)] = username
			await ctx.send(f":white_check_mark: **{ctx.message.author}, your `Bancho` username has been edited to `{username}`**")
		else:
			await ctx.send(f'`{username}` **doesn\'t exist in the** `Bancho` **database.**')

gamemode_texts = {
	"osu": 'osu! Standard',
	"taiko": 'Taiko',
	"fruits": 'Catch The Beat!',
	"mania": 'osu! Mania'
}

rank_emotes_index = [
	"<:EmoteName:1119272076730175558>", # SSH
	"<:EmoteName:1119272089971605504>", # SS
	"<:EmoteName:1119272112138506331>", # SH
	"<:EmoteName:1119272128055881739>", # S
	"<:EmoteName:1119272145567092756>", # A
	"<:EmoteName:1119272157965463573>", # B
	"<:EmoteName:1119272169424310384>", # C
	"<:EmoteName:1119272235945963590>", # D
	"<:EmoteName:1119272252337295420>"  # F
]

def build_profile_embed(ctx, profile_info, mode):
	try: # if ctx is actually a message object like for link detection
		server_user = ctx.message.author
	except:
		server_user = ctx.author
	# embed
	em = discord.Embed(description = '', colour = server_user.colour)
	gamemode_text = gamemode_texts[mode]
	username = profile_info['username']
	url_username = username.replace(' ', '%20')
	country_code = profile_info['country_code']
	em.set_author(name = f"{gamemode_text} Profile for {username}", icon_url = f'https://osu.ppy.sh/images/flags/{country_code}.png', url = f'https://osu.ppy.sh/users/{url_username}/{mode}')
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
		for i in range(5):
			rank_emote = rank_emotes_index[i]
			rank_count = profile_info['ranks'][i]
			info += f'{rank_emote}`{rank_count}`'
		info += "\n"
	em.description = info

	# footer
	verified = " | Verified" if profile_info['is_verified'] else ""
	if profile_info['is_online']:
		em.set_footer(text = f"On osu! Bancho Server{verified}", icon_url = "https://i.imgur.com/DKLGecZ.png")
	else:
		last_seen = profile_info['last_seen']
		em.set_footer(text = f"Last Seen {last_seen} Ago on osu! Bancho{verified}", icon_url = "https://i.imgur.com/sOtDO3u.png")
	
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

@bot.command()
async def osu(ctx, username=None):
	await card_cmd(ctx, username, 'osu')

@bot.command()
async def taiko(ctx, username=None):
	await card_cmd(ctx, username, 'taiko')

@bot.command()
async def ctb(ctx, username=None):
	await card_cmd(ctx, username, 'fruits')

@bot.command()
async def mania(ctx, username=None):
	await card_cmd(ctx, username, 'mania')

########################################### recent ###########################################

recent_mode_aliases = {
	'osu': ['osu', 'std', 'standard', '0'],
	'taiko': ['taiko', 'drum', 'drums', '1'],
	'fruits': ['fruits', 'ctb', 'catch', '2'],
	'mania': ['mania', 'piano', '3']
}

def format_options(options, tabs=1):
	text = '\n'
	for key, values in options.items():
		text += '\t'*tabs+f'{key}: '
		for i in range(len(values)-1):
			text += values[i]+', '
		text += values[-1]+'\n'
	return text

recent_mode_aliases_text = format_options(recent_mode_aliases, 9)
recent_help_msg = code_to_txt(
f'''
Usage: ~rs <username>
Arguments:
	-l|list 					List most recent scores.
	-b|best 					Get most recent score in top 100.
	-?|search|find 	<map name>	Search <map name> in recent scores.
	-i|index 		<index>		Get score <index> from recents. (1-100)
	-m|mode 		<mode>		modes aliases:{recent_mode_aliases_text}
'''
)

rank_emotes_string = {
	"XSH": "<:EmoteName:1119272076730175558>",
	"XS": "<:EmoteName:1119272089971605504>",
	"SH": "<:EmoteName:1119272112138506331>",
	"S": "<:EmoteName:1119272128055881739>",
	"A": "<:EmoteName:1119272145567092756>",
	"B": "<:EmoteName:1119272157965463573>",
	"C": "<:EmoteName:1119272169424310384>",
	"D": "<:EmoteName:1119272235945963590>",
	"F": "<:EmoteName:1119272252337295420>"
}

def build_recent_embed(ctx, recent_info, mode):

	user_info = recent_info['user']
	# beatmap_info = recent_info['beatmap']
	beatmap_info = osu_api.beatmap_info(recent_info['beatmap']['id'])

	server_user = ctx.message.author

	msg = f'**Recent {gamemode_texts[mode]} Play for {user_info['username']}:**'
	info = ""

	stats = recent_info['statistics']
	progress = (stats['count_300']+stats['count_100']+stats['count_50']+stats['count_miss'])/(beatmap_info['count_circles']+beatmap_info['count_sliders']+beatmap_info['count_spinners'])*100 if recent_info['rank'] == 'F' else ''
	pp_text = 
	if user_recent['rank'] == 'F':
		info += f'▸ {rank_emotes_string[user_recent['rank']]} ({progress:.1f}%) ▸ **{score_pp(user_recent, beatmap_info['id']):.2f}** ({score_pp(user_recent, beatmap_info['id'], beatmap_info['max_combo']):.2f}) ▸ {user_info['accuracy']*100:.2f}%\n'
	else:
		info += f'▸ {rank_emotes_string[user_recent['rank']]} ▸ **{score_pp(user_recent, beatmap_info['id']):.2f}** ({score_pp(user_recent, beatmap_info['id'], beatmap_info['max_combo']):.2f}) ▸ {user_info['accuracy']*100:.2f}%\n'

	em = discord.Embed(description=info, colour=server_user.colour)
	em.set_author(
		name=f'{beatmap_info['title']} [{beatmap_info['version']}]{...} +{beatmap_info['mods']} [{beatmap_info['difficulty_rating']}]', 
		url=f'https://osu.ppy.sh/beatmapsets/{beatmap_info['beatmapset_id']}#{beatmap_info['mode']}/{beatmap_info['id']}',
		icon_url=osu_api.user_info(username)['avatar_url'])
	em.set_thumbnail(url=f'https://b.ppy.sh/thumb/{beatmap_info['1151942']}l.jpg')

	try:
		play_time = datetime.datetime.strptime(recent_info['date'], '%Y-%m-%d %H:%M:%S')
	except:
		play_time = datetime.datetime.strptime(recent_info['date'], '%Y-%m-%dT%H:%M:%S+00:00')
	
	try:
		timeago = utils.time_ago(datetime.datetime.utcnow(), play_time, shift=0)
	except:
		try:
			timeago = utils.time_ago(datetime.datetime.utcnow(), play_time, shift=2)
		except:
			timeago = utils.time_ago(datetime.datetime.utcnow(), play_time, shift=8)

	attempt = ""
	if attempt_num:
		attempt = "Try #{} | ".format(attempt_num)

	server_name = self.owoAPI.get_server_name(api)
	server_icon_url = self.owoAPI.get_server_avatar(api)
	em.set_footer(text = "On osu! {} Server".format(server_name),
		icon_url=self.owoAPI.get_server_avatar(api))

	em.set_footer(text = "{}{}Ago On osu! {} Server".format(attempt, timeago, server_name),
		icon_url=server_icon_url)

	return (msg, em, graph_file)


async def send_recent_card(ctx, username, mode):
	user_recent = osu_api.user_recent(username)
	if user_recent == []:
		await ctx.send(f'**`{username}` has no recent plays in `Bancho` for `{gamemode_texts[mode]}`.**')
	else:
		embed = build_recent_embed(ctx, user_recent, mode)
		await ctx.send(embed=embed)

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

	# search
	search = None
	search_index = args.get('-?')
	if search_index == -1: search_index = args.get('-search')
	if search_index == -1: search_index = args.get('-find')
	if search_index != -1:
		if search_index+1 < len(args):
			search = args[search_index+1]
			indexes.delete(search_index)
			indexes.delete(search_index+1)
		else:
			ctx.send(recent_help_msg)
			return False, _

	# index
	index = None
	index_index = args.get('-i')
	if index_index == -1: index_index = args.get('-index')
	if index_index != -1:
		if index_index+1 < len(args):
			index = args[index_index+1]
			try:
				index = int(index)
			except:
				ctx.send(recent_help_msg)
				return False, _
			if index < 1 or index > 100:
				ctx.send(recent_help_msg)
				return False, _
			indexes.delete(index_index)
			indexes.delete(index_index+1)
		else:
			ctx.send(recent_help_msg)
			return False, _

	# mode
	mode = None
	mode_index = args.get('-m')
	if mode_index == -1: mode_index = args.get('mode')
	if mode_index != -1:
		if mode_index+1 < len(args):
			mode = match_aliases(args[mode_index+1], recent_mode_aliases)
			if not mode:
				await ctx.send(recent_help_msg)
				return False, _
			indexes.delete(mode_index)
			indexes.delete(mode_index+1)
		else:
			await ctx.send(recent_help_msg)
			return False, _
	
	# everything left is considered as username
	usernames = [args[index] for index in indexes]

	return True, usernames, mode, best, index, list_, search

@bot.command()
async def rs(ctx):
	success, usernames, mode, best, index, list_, search = await parse_recent_arguments(ctx)
	if not success: return
	if len(usernames) == 0:
		usernames = [users.get(str(ctx.message.author.id))]
		if not usernames[0]:
			await ctx.send('First use `~osuset <osu! pseudo>`')
	if mode:
		for username in usernames:
			if osu_api.exists(username):
				await send_recent_card(ctx, username, mode)
			else:
				await ctx.send(f':red_circle: **`{username}` not found.**')
	else:
		for username in usernames:
			user_info = osu_api.user_info(username)
			if user_info:
				await send_recent_card(ctx, username, user_info['playmode'])
			else:
				await ctx.send(f':red_circle: **`{username}` not found.**')

########################################### recent ###########################################

bot.run(str(open('secrets/token', 'r').read()))
