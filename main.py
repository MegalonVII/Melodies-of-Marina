# all imports
import discord
from discord.ext import commands
from datetime import datetime
from sys import exit
from pytz import timezone
import os
from dotenv import load_dotenv

# token init
load_dotenv()
token = os.getenv('TOKEN')

# bot initalization starts here
bot = commands.Bot('m.', intents=discord.Intents.all())
bot.remove_command('help')

# log in time determinant
def get_login_time(tz: str) -> str:
    return f"Time: {datetime.now(timezone(tz)).strftime('%m/%d/%Y, %I:%M:%S %p')}\nTimezone: {tz}\n"

# log in process
@bot.event
async def on_ready():
  print("\nLoading music extension...")
  try: # music ext set up
    await bot.load_extension('music')
    print("Extension loaded! Setting presence...")
  except:
    print("Unable to load. Terminating...")
    exit(0)
  try: # presence set up
    await bot.change_presence(activity=discord.Game(name="your absolute jammers in chat! | /help"))
    print("Presence set! Syncing commands...")
  except:
    print("Unable to set presence. Terminating...")
    exit(0)
  try: # app tree set up
    print(f"Synced {len(await bot.tree.sync())} command(s)! Logging in...")
  except:
    print("Unable to sync. Terminating...")
    exit(0)
  return print(f'\nLogged in as: {bot.user.name}\nID: {bot.user.id}\n' + get_login_time('US/Eastern'))

# help command
@bot.hybrid_command(name="help", description="Get help pertaining to all commands!")
async def help(ctx):
  e = discord.Embed(color=discord.Color.green())
  e.set_author(name='Commands Available')

  e.add_field(name='/join', value='Joins the voice chat that you are in', inline=False)
  e.add_field(name='/leave', value='Leaves the voice chat that I am in', inline=False)
  e.add_field(name='/play (YouTube URL or search query)', value= 'While I\'m in voice call, I will play the song from the YouTube URL or search query you provide me.', inline=False)
  e.add_field(name='/now', value='Displays the current song that I\'m playing', inline=False)
  e.add_field(name='/queue (optional: page number)', value='Displays the queue of songs. Page value defaults to 1. Each page displays the first 25 songs in the queue', inline=False)
  e.add_field(name='/shuffle', value='Shuffles the current queue. *[DJs/Admin Only]*', inline=False)
  e.add_field(name='/remove (index)', value='Removes the song at the provided index from the queue', inline=False)
  e.add_field(name='/pause', value='Pauses any music that I\'m playing', inline=False)
  e.add_field(name='/resume', value='Resumes any paused music', inline=False)
  e.add_field(name='/stop', value='Stops any playing music entirely', inline=False)
  e.add_field(name='/skip', value='Skips the current playing song to the next one in the queue. Only the song requester can do this, though DJs and Admins are unaffected', inline=False)
  e.set_footer(text='If I stop working midway through your voice call, please contact Megalon, as they need to restart me')

  return await ctx.reply(embed=e, mention_author=False, ephemeral=True)

# command error
@bot.event
async def on_command_error(ctx, error):
  return await ctx.reply(f'Uh oh! Try "/help"... ({error})', mention_author=False)

# run process
bot.run(token)