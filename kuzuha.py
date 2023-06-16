# invite url
'''
https://discord.com/api/oauth2/authorize?client_id=1103140474375647303&permissions=8&redirect_uri=https%3A%2F%2Fdiscord.com%2F&response_type=code&scope=applications.commands%20bot%20guilds%20guilds.members.read%20identify%20messages.read
'''

from osu_api import *
import discord
from discord.ext import commands

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
		user_exists, user_info = osu_api.get_user_info(username)
		if user_exists:
			users[str(ctx.message.author.id)] = (username, user_info['playmode'])
			await ctx.send(f":white_check_mark: **{ctx.message.author}, your `Bancho` username has been edited to `{username}`**")
		else:
			await ctx.send(f'`{username}` **doesn\'t exist in the** `Bancho` **database.**')

gamemode_texts = {
	"osu": 'osu! Standard',
	"taiko": 'Taiko',
	"fruits": 'Catch The Beat!',
	"mania": 'osu! Mania'
}

rank_emotes = [
	":hearts:", # SSH
	":thumbsup:", # SS
	":ok_hand:", # SH
	":no_entry_sign:", # S
	":x:" # A
]

async def build_osu_profile_embed(ctx, user_info, mode):
	try: # if ctx is actually a message object like for link detection
		server_user = ctx.message.author
	except:
		server_user = ctx.author
	# embed
	em = discord.Embed(description = '', colour = server_user.colour)
	gamemode_text = gamemode_texts[mode]
	username = user_info['username']
	url_username = username.replace(' ', '%20')
	country_code = user_info['country_code']
	em.set_author(name = f"{gamemode_text} Profile for {username}", icon_url = f'https://osu.ppy.sh/images/flags/{country_code}.png', url = f'https://osu.ppy.sh/users/{url_username}/{mode}')
	em.set_thumbnail(url = user_info['avatar_url'])
	
	bancho_rank = user_info['bancho_rank']
	peak_rank = user_info['peak_rank']
	peak_rank_achieved = user_info['peak_rank_achieved']
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
		info += f"▸ **Peak Rank:** #{peak_rank:,} achieved `{peak_rank_achieved}`\n"

	info += f"▸ **Level:** {level} + {level_progress:.2f}%\n"
	info += f"▸ **PP**: {pp:,} **Acc**: {round(acc, 2)}%\n"
	if playcount == 0:
		info += f"▸ **Playcount:** {playcount:,}\n"
	else:
		info += f"▸ **Playcount:** {playcount:,} ({playcount_hours:,} hrs)\n"
	if not user_info['ranks_all_zero']:
		info += f"▸ **Ranks:** "
		for i in range(5):
			rank_emote = rank_emotes[i]
			rank_count = user_info['ranks'][i]
			info += f'{rank_emote}`{rank_count}`'
		info += "\n"
	em.description = info

	# footer
	verified = " | Verified" if user_info['is_verified'] else ""
	if user_info['is_online']:
		em.set_footer(text = f"On osu! Bancho Server{verified}", icon_url = "https://i.imgur.com/DKLGecZ.png")
	else:
		last_seen = user_info['last_seen']
		em.set_footer(text = f"Last Seen {last_seen} Ago on osu! Bancho{verified}", icon_url = "https://i.imgur.com/sOtDO3u.png")
	
	return em

async def send_user_card(ctx, username, mode):
	user_exists, user_info = osu_api.get_user_info(username, mode=mode)
	if user_exists:
		embed = await build_osu_profile_embed(ctx, user_info, mode)
		await ctx.send(embed=embed)
	else:
		await ctx.send(f':red_circle: `{username}` **not found.**')

async def card_cmd(ctx, username, mode):
	if username == '':
		pair = users.get(str(ctx.message.author.id))
		if pair != None:
			await send_user_card(ctx, pair[0], pair[1] if mode == 'osu' else mode)
		else:
			await ctx.send('First use `~osuset <osu! pseudo>`')
	else:
		await send_user_card(ctx, username, mode)

@bot.command()
async def osu(ctx, username=''):
	await card_cmd(ctx, username, 'osu')

@bot.command()
async def taiko(ctx, username=''):
	await card_cmd(ctx, username, 'taiko')

@bot.command()
async def ctb(ctx, username=''):
	await card_cmd(ctx, username, 'fruits')

@bot.command()
async def mania(ctx, username=''):
	await card_cmd(ctx, username, 'mania')

bot.run(str(open('token', 'r').read()))
