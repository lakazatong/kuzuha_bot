from kuzuha import *

######### events #########

@bot.event
async def on_ready():
	await load_users()
	cprint(f'Logged in as {bot.user.name} ({bot.user.id})', GREEN)

######### owner #########

# closes the bot
@bot.command(aliases=['q'])
@commands.is_owner()
async def quit(ctx):
	global osu_api
	osu_api.close()
	await save_users()
	await bot.close()

######### system #########

# restarts the bot
@bot.command(aliases=['r'])
async def restart(ctx):
	await ctx.message.delete()
	os.execv(sys.executable, ['python3'] + sys.argv)

# sends users json
@bot.command()
async def send_users(ctx):
	r = await ctx.send(json.dumps(get_users(), indent=3))
	print(type(r))

######### osu #########

# registers a new user
@bot.command(aliases=['userset', 'set', 'setuser'])
async def osuset(ctx, username=None):
	if username:
		await osuset_cmd(ctx, username)
	else:
		await ctx.send('`Usage: ~osuset <osu! pseudo>`')

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

recent_help = load_raw('messages/help/recent')

# recent plays
@bot.command(aliases=['rs'])
async def recent(ctx):
	arguments, options = parse(ctx.message.content, recent_options)
	if options[0]:
		create_message(recent_help, ctx.channel.id)
		# await ctx.send(embed=recent_help_embed)
		return
	
	if len(usernames) == 0:
		usernames = [get_username(ctx.message.author.id)]
		if not usernames[0]:
			await ctx.send('First use `~osuset <osu! pseudo>`')
			return
	for username in usernames:
		await send_user_recent_card(ctx, username, *args)

######### fun #########

ansi_options = {
	# format:
	# "short": [takes_arg, longs]
	"h": [False, 'help'],
	"f": [True, 'format', 'esc-format'],
	"s": [True, 'escape', 'esc'],
	"e": [True, 'end'],
	"b": [False, 'black_bg', 'black']
}

ansi_msg = json.loads(load_raw('messages/ansi'))

@bot.event
async def on_button_click(interaction):
	print('clicked_done')
	print(interaction.message.interaction == interaction)
	# await interaction.message.clear_reactions()
	# interaction.message.clicked_done = True

@bot.command()
async def ansi(ctx):
	# ctx.message.clicked_done = False

	arguments, options = parse(ctx.message.content, ansi_options)
	if options[0]:
		await ctx.send('ansi help msg')
		return

	out = capture_console_output(ansi_text, ' '.join(ctx.message.content.split(' ')[1:]), *options[1:])
	ansi_msg['content'] = '```ansi\n'+out+'```'
	msg = create_message(ansi_msg, ctx.channel.id, channel=ctx.channel)
	wait = 0
	last_edit_time = ctx.message.created_at
	while True:
		await asyncio.sleep(1)
		print(f'ansi: waiting {ctx.message.author.name}... '+str(wait))
		wait += 1
		if wait == 30: break
		# if ctx.message.clicked_done: break
		async for entry in ctx.channel.history(limit=1, before=msg):
			if not entry.edited_at or entry.edited_at == last_edit_time or (entry.edited_at - last_edit_time).total_seconds() >= 60:
				continue
			out = capture_console_output(ansi_text, ' '.join(entry.content.split(' ')[1:]), *options[1:])
			ansi_msg['content'] = '```ansi\n'+out+'```'
			await msg.edit(content='```ansi\n'+out+'```')
			wait = 0
			last_edit_time = entry.edited_at
			break

bot.run(discord_bot_token)