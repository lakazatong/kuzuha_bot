from kuzuha import *

######### events #########

@bot.event
async def on_ready():
	await load_users()
	cprint(f'Logged in as {bot.user.name} ({bot.user.id})', GREEN)

######### system #########

# closes the bot
@bot.command(aliases=['q'])
@commands.is_owner()
async def quit(ctx):
	await close()
	await ctx.message.add_reaction('👋')
	await bot.close()

# restarts the bot
@bot.command(aliases=['r'])
@commands.is_owner()
async def restart(ctx):
	await close()
	await ctx.message.delete()
	os.execv(sys.executable, ['python3'] + sys.argv)

# sends users json
@bot.command()
async def send_users(ctx):
	await ctx.channel.send(json.dumps(get_users(), indent=3))

# help message
# @bot.command()
# async def help(ctx):
# 	create_message(global_help, channel=ctx.channel)

######### osu #########

# registers a new user
@bot.command(aliases=['userset', 'set', 'setuser'])
async def osuset(ctx, username=None):
	if username:
		await osuset_cmd(ctx, username)
	else:
		await ctx.channel.send('`Usage: ~osuset <osu! pseudo>`')

# osu profile
@bot.command(aliases=['std', 'standard'])
async def osu(ctx, username=None):
	await card_cmd(ctx, username, 'osu')

# taiko profile
@bot.command(aliases=['drum', 'drums'])
async def taiko(ctx, username=None):
	await card_cmd(ctx, username, 'taiko')

# ctb profile
@bot.command(aliases=['fruits', 'catch'])
async def ctb(ctx, username=None):
	await card_cmd(ctx, username, 'fruits')

# mania profile
@bot.command(aliases=['piano', 'tiles'])
async def mania(ctx, username=None):
	await card_cmd(ctx, username, 'mania')

# recent plays
@bot.command(aliases=['rs'])
async def recent(ctx):
	active = True
	arguments, options = parse(ctx.message.content, recent_options)
	if options[0]:

		view = discord.ui.View(timeout=300)
		view.interaction_check = is_author
		view.add_item(ACTIVE_BUTTON)
		async def ansi_view_timetout():
			nonlocal active
			active = False
		view.on_timeout = ansi_view_timetout
		msg = await ctx.channel.send('', view=view)
		while active:

			...
		return
	
	await recent_cmd(ctx, arguments, *options[1:])

######### fun #########

@bot.command()
async def ansi(ctx):
	global running_tasks
	arguments, options = parse(ctx.message.content, ansi_options)
	if options[0]:
		await ctx.channel.send('ansi help msg')
		return
	running_tasks.add(asyncio.create_task(ansi_cmd(ctx, arguments, *options[1:])))

@bot.command()
async def avatar(ctx):
	arguments, options = parse(ctx.message.content, avatar_options)
	if options[0]:
		ctx.channel.send('avatar help')
		return
	await avatar_cmd(ctx, [str(ctx.message.author.id)], *options[1:]) if arguments == [] else await avatar_cmd(ctx, arguments, *options[1:])


bot.run(discord_bot_token)