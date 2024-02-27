from discord.ext import commands
import asyncio
from colorama import Fore, Style, Back
from helpers.songqueue import SongQueue
from helpers.errors import VoiceError

class VoiceState:
    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        self.bot = bot
        self._ctx = ctx
        self.current = None
        self.voice = None
        self.next = asyncio.Event()
        self.songs = SongQueue()
        self._loop = False
        self._volume = 0.5
        self.skip_votes = set()
        self.audio_player = bot.loop.create_task(self.audio_player_task())

    def __del__(self):
        self.audio_player.cancel()

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = value

    @property
    def is_playing(self):
        return self.voice and self.current

    async def audio_player_task(self):
        while True:
            self.next.clear()
            try:
                self.current = await self.songs.get()
            except:
                self.bot.loop.create_task(self.stop())
                return
            self.current.source.volume = self._volume
            self.voice.play(self.current.source, after=self.play_next_song)
            print(f'{Style.BRIGHT}Playing {Style.RESET_ALL}{Back.MAGENTA}{Fore.RED}{self.current.source.__str__()[2:-2]}{Back.RESET}{Fore.RESET} in {Style.RESET_ALL}{Fore.BLUE}{self.voice.channel.name}{Fore.RESET}{Style.BRIGHT} in {Style.RESET_ALL}{Fore.GREEN}{self.voice.channel.guild.name} ({self.voice.channel.guild.id}){Fore.RESET}')
            await self.current.source.channel.send(embed=self.current.create_embed())
            await self.next.wait()

    def play_next_song(self, error=None):
        if error:
            VoiceError(str(error))
        self.next.set()

    def skip(self):
        self.skip_votes.clear()
        if self.is_playing:
            self.voice.stop()

    async def stop(self):
        self.songs.clear()
        if self.voice:
            await self.voice.disconnect()
            self.voice = None