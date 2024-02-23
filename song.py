import discord
from ytdlsource import YTDLSource

class Song:
    __slots__ = ('source', 'requester')

    def __init__(self, source: YTDLSource):
        self.source = source
        self.requester = source.requester

    def create_embed(self):
        embed = (discord.Embed(title='Now playing', description=f'**{self.source.title}**', color=discord.Color.green())
            .add_field( name='Duration', value=self.source.duration)
            .add_field(name='Requested by', value=self.requester.mention)
            .set_thumbnail(url=self.source.thumbnail))
        return embed