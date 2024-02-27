import discord
import yt_dlp as youtube_dl
from discord.ext import commands
import asyncio
import functools
from helpers.errors import YTDLError

youtube_dl.utils.bug_reports_message = lambda: ''

class YTDLSource(discord.PCMVolumeTransformer):
    YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
    }

    FFMPEG_OPTIONS = {
        'before_options':
        '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

    def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, data: dict, volume: float = 0.5):
        super().__init__(source, volume)
        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')
        self.duration = self.parse_duration(int(data.get('duration')))
        self.tags = data.get('tags')
        self.url = data.get('webpage_url')

    def __str__(self):
        return f'**{self.title}**'

    @classmethod
    async def create_source(cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None):
        loop = loop or asyncio.get_event_loop()
        partial = functools.partial(cls.ytdl.extract_info, search, download=False, process=False)
        data = await loop.run_in_executor(None, partial)

        if data is None:
            return await ctx.reply(f"Uh oh! Couldn\'t find anything that matches `{search}`...", mention_author=False)
        if 'entries' not in data:
            process_info = data
        else:
            process_info = None
            for entry in data['entries']:
                if entry:
                    process_info = entry
                    break
            if process_info is None:
                return await ctx.reply(f"Uh oh! Couldn\'t find anything that matches `{search}`...", mention_author=False)

        webpage_url = process_info['webpage_url']
        partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            raise YTDLError(f"Uh oh! Couldn\'t fetch `{webpage_url}`...")

        if 'entries' not in processed_info:
            info = processed_info
        else:
            info = None
        while info is None:
            try:
                info = processed_info['entries'].pop(0)
            except IndexError:
                return await ctx.reply(f'Uh oh! Couldn\'t retrieve any matches for `{webpage_url}`...', mention_author=False)

        return cls(ctx, discord.FFmpegPCMAudio(info['url'], **cls.FFMPEG_OPTIONS), data=info)

    @staticmethod
    def parse_duration(duration: int):
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        duration = []
        if days > 0:
            duration.append('1 day' if days == 1 else f'{days} days')
        if hours > 0:
            duration.append('1 hour' if hours == 1 else f'{hours} hours')
        if minutes > 0:
            duration.append('1 minute' if minutes == 1 else f'{minutes} minutes')
        if seconds > 0:
            duration.append('1 seconds' if seconds == 1 else f'{seconds} seconds')
        return ', '.join(duration)