from kuzuha import *

@bot.event
async def on_ready():
	await load_users()
	# await bot.get_channel(1030917130218123414).send(embed=recent_help_embed)
	# create_message(load_raw_message('raw'), 1030917130218123414)
	# create_message(read_file('raw'), 1030917130218123414)
	cprint(f'Logged in as {bot.user.name} ({bot.user.id})', GREEN)

@bot.command(aliases=['r'])
async def restart(ctx):
	await ctx.message.delete()
	os.execv(sys.executable, ['python3'] + sys.argv)

@bot.command(aliases=['q'])
@commands.is_owner()
async def quit(ctx):
	global osu_api
	osu_api.close()
	await save_users()
	await bot.close()

@bot.command()
async def send_users(ctx):
	await ctx.send(json.dumps(get_users(), indent=3))

@bot.command(aliases=['userset', 'set', 'setuser'])
async def osuset(ctx, username=None):
	if username:
		await osuset_cmd(ctx, username)
	else:
		await ctx.send('`Usage: ~osuset <osu! pseudo>`')

@bot.command(aliases=['std', 'standard'])
async def osu(ctx, username=None):
	await card_cmd(ctx, username, 'osu')

@bot.command(aliases=['drum', 'drums'])
async def taiko(ctx, username=None):
	await card_cmd(ctx, username, 'taiko')

@bot.command(aliases=['fruits', 'catch'])
async def ctb(ctx, username=None):
	await card_cmd(ctx, username, 'fruits')

@bot.command(aliases=['piano', 'tiles'])
async def mania(ctx, username=None):
	await card_cmd(ctx, username, 'mania')

@bot.command(aliases=['rs'])
async def recent(ctx):
	success, usernames, args = await parse_recent_arguments(ctx)
	if not success:
		await ctx.send(embed=recent_help_embed)
		return
	if len(usernames) == 0:
		usernames = [get_username(ctx.message.author.id)]
		if not usernames[0]:
			await ctx.send('First use `~osuset <osu! pseudo>`')
			return
	for username in usernames:
		await send_user_recent_card(ctx, username, *args)

bot.run(discord_bot_token)