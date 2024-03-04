import discord
from discord.ext import commands
from discord import app_commands
import math
from colorama import Fore, Style
import nacl
from helpers.voicestate import VoiceState
from helpers.song import Song
from helpers.ytdlsource import YTDLSource
from helpers.errors import YTDLError
from helpers.functions import parse_total_duration

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_states = {}

    # frontend helpers
    # these functions make the bot act according to certain contexts, such as being used in dms or being used as an interaction
    async def respond(self, ctx: commands.Context, message: str, emoji: str):
        try:
            return await ctx.message.add_reaction(emoji)
        except:
            return await ctx.reply(f"{message} {emoji}", mention_author=False)

    async def cog_check(self, ctx: commands.Context) -> bool:
        if not ctx.guild:
            return False
        return True
    
    # backend helpers
    # this is to initiate the voice call that the bot will be in
    def get_voice_state(self, ctx: commands.Context):
        state = self.voice_states.get(ctx.guild.id)
        if not state:
            state = VoiceState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state
        return state

    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)

    # commands that are usable
    # join, leave, now, pause, resume, stop, skip, queue, shuffle, remove, play
    @commands.hybrid_command(name='join', description="Joins your voice call!")
    async def _join(self, ctx: commands.Context):
        destination = ctx.author.voice.channel if ctx.author.voice else None 
        try:
            ctx.voice_state.voice = await destination.connect()
            print(f'{Style.BRIGHT}Joined {Style.RESET_ALL}{Fore.BLUE}{ctx.author.voice.channel.name}{Fore.RESET}{Style.BRIGHT} in {Style.RESET_ALL}{Fore.GREEN}{ctx.author.guild.name} ({ctx.author.guild.id}){Fore.RESET}')
            return await self.respond(self, ctx, f'Joined `{ctx.author.voice.channel.name}`!', '✅')
        except:
            return await ctx.reply('Uh oh! I couldn\'t connect to your voice channel. Maybe you\'re not in one or I\'m in a different one...', mention_author=False, ephemeral=True)
      
    @commands.hybrid_command(name='leave', description="Leaves your voice call!")
    async def _leave(self, ctx: commands.Context):
        if not ctx.voice_state.voice:
            return await ctx.reply('Uh oh! I\'m not connected to any voice channel...', mention_author=False)
        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel or ctx.author.voice is None:
                return await ctx.reply('Uh oh! You\'re not in my voice channel...', mention_author=False)
        await ctx.voice_state.stop()
        print(f'{Style.BRIGHT}Left {Style.RESET_ALL}{Fore.BLUE}{ctx.author.voice.channel.name}{Fore.RESET}{Style.BRIGHT} in {Style.RESET_ALL}{Fore.GREEN}{ctx.author.guild.name} ({ctx.author.guild.id}){Fore.RESET}')
        del self.voice_states[ctx.guild.id]
        return await self.respond(self, ctx, 'Goodbye!', '👋')

    @commands.hybrid_command(name='now', description="Shows what's now playing!")
    async def _now(self, ctx: commands.Context):
        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
            return await ctx.reply(embed=ctx.voice_state.current.create_embed(), mention_author=False)
        else:
            return await ctx.reply('Uh oh! I\'m currently not playing anything...', mention_author=False, ephemeral=True)

    @commands.hybrid_command(name='pause', description="Pauses the jams!")
    async def _pause(self, ctx: commands.Context):
        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel or ctx.author.voice is None:
                return await ctx.reply('Uh oh! You\'re not in my voice channel...', mention_author=False, ephemeral=True)
        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
            ctx.voice_state.voice.pause()
            return await self.respond(self, ctx, 'Paused!', '⏸️')
        else:
            return await ctx.reply('Uh oh! Nothing to pause...', mention_author=False, ephemeral=True)

    @commands.hybrid_command(name='resume', description="Resumes the jams!")
    async def _resume(self, ctx: commands.Context):
        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel or ctx.author.voice is None:
                return await ctx.reply('Uh oh! You\'re not in my voice channel...', mention_author=False, ephemeral=True)
        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_paused():
            ctx.voice_state.voice.resume()
            return await self.respond(self, ctx, 'Resumed!', '▶️')
        else:
            return await ctx.reply('Uh oh! Nothing to resume...', mention_author=False, ephemeral=True)

    @commands.hybrid_command(name='stop', description="Stops the music and clears the queue!")
    async def _stop(self, ctx: commands.Context):
        if ctx.voice_client:
            if ctx.author.voice and ctx.voice_client.channel != ctx.author.voice.channel or ctx.author.voice is None:
                return await ctx.reply('Uh oh! You\'re not in my voice channel...', mention_author=False, ephemeral=True)
        if ctx.voice_state.is_playing:
            ctx.voice_state.songs.clear()
            ctx.voice_state.voice.stop()
            return await self.respond(self, ctx, 'Stopped!', '⏹️')
        else:
            return await ctx.reply('Uh oh! I\'m not playing any music right now...', mention_author=False, ephemeral=True)

    @commands.hybrid_command(name='skip', description="Skip to the next song in the queue!")
    async def _skip(self, ctx: commands.Context):
        voter = ctx.message.author
        djRole = discord.utils.get(ctx.guild.roles, name="DJ")
        if ctx.voice_client:
            if ctx.voice_client.channel != voter.voice.channel or voter.voice is None:
                return await ctx.reply('Uh oh! You\'re not in my voice channel...', mention_author=False, ephemeral=True)
        if not ctx.voice_state.is_playing:
            return await ctx.reply('Uh oh! I\'m not playing any music right now...', mention_author=False, ephemeral=True)
        if voter == ctx.voice_state.current.requester or djRole in voter.roles or voter.guild_permissions.administrator:
            ctx.voice_state.skip()
            return await self.respond(self, ctx, 'Skipped!', '⏭️')
        else:
            return await ctx.reply('Uh oh! You didn\'t request this song to be played (DJs and adminstrators are unaffected)...', mention_author=False)

    @commands.hybrid_command(name='queue', description="Shows the queue! Enter a number as well to see which page in the queue!")
    @app_commands.describe(page="Queue page")
    async def _queue(self, ctx: commands.Context, *, page: int = 1):
        if page < 1:
            return await ctx.reply('Uh oh! Invalid page number. Must be greater than or equal to `1`...', mention_author=False, ephemeral=True)
        if len(ctx.voice_state.songs) == 0:
            return await ctx.reply('Uh oh! Queue is empty...', mention_author=False, ephemeral=True)
        items_per_page = 25
        pages = math.ceil(len(ctx.voice_state.songs) / items_per_page)
        if page > pages:
            return await ctx.reply(f'Uh oh! Invalid page number. Must be less than or equal to `{pages}`...', mention_author=False, ephemeral=True)
        start = (page - 1) * items_per_page
        end = start + items_per_page
        queue = ''
        total_duration = []
        for i, song in enumerate(ctx.voice_state.songs[start:end], start=start):
            queue += f'`{i+1}.` **{song.source.title}** (*{song.source.duration}*)\n'
            total_duration.append(song.source.duration) 
        embed = (discord.Embed(color=discord.Color.green(),description=f'**{len(ctx.voice_state.songs)} tracks:**\n\n{queue}')
                .set_footer(text=f'Viewing page {page}/{pages}\nTotal Queue Duration: {parse_total_duration(total_duration)}'))
        return await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(name='shuffle', description="Shuffles the queue!")
    async def _shuffle(self, ctx: commands.Context):
        author = ctx.message.author
        djRole = discord.utils.get(ctx.guild.roles, name="DJ")

        if ctx.voice_client:
            if ctx.voice_client.channel != author.voice.channel or author.voice is None:
                return await ctx.reply('Uh oh! You\'re not in my voice channel...', mention_author=False)
        if author.guild_permissions.administrator or djRole in author.roles:
            if len(ctx.voice_state.songs) == 0:
                return await ctx.reply('Uh oh! Queue is empty...', mention_author=False)
            else:
                ctx.voice_state.songs.shuffle()
                return await self.respond(self, ctx, 'Queue shuffled!', '🔀')
        else:
            return await ctx.reply('Uh oh! You don\'t have the permissions to use this. Must be either a DJ or administrator...', mention_author=False)

    @commands.hybrid_command(name='remove', description="Removes the specified numeric entry from the queue!")
    @app_commands.describe(index="Queue index to remove")
    async def _remove(self, ctx: commands.Context, index: int):
        queue = ctx.voice_state.songs
        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel or ctx.author.voice is None:
                return await ctx.reply('Uh oh! You\'re not in my voice channel...', mention_author=False, ephemeral=True)
        if len(queue) == 0:
            return await ctx.reply('Uh oh! Queue is empty...', mention_author=False, ephemeral=True)
        elif index < 0 or index == 0 or index > len(queue):
            return await ctx.reply('Uh oh! Index out of bounds...', mention_author=False, ephemeral=True)
        ctx.voice_state.songs.remove(index - 1)
        return await self.respond(self, ctx, 'Song removed from queue!', '✅')

    @commands.hybrid_command(name='play', description="Plays some tunes!")
    async def _play(self, ctx: commands.Context, *, search: str):
        if not ctx.voice_state.voice:
            return await ctx.reply('Uh oh! I\'m not connected to a voice channel...', mention_author=False, ephemeral=True)
        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                return await ctx.reply('Uh oh! I\'m already in a voice channel...', mention_author=False, ephemeral=True)
        async with ctx.typing():
            try:
                source = await YTDLSource.create_source(ctx, search)
            except YTDLError as e:
                return await ctx.reply(f'Uh oh! An error occurred while processing this request... ({str(e)})', mention_author=False, ephemeral=True)
            else:
                song = Song(source)
                await ctx.voice_state.songs.put(song)
                return await ctx.reply(f'Queued {str(source)}', mention_author=False)

async def setup(bot):
    await bot.add_cog(Music(bot))