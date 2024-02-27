"""
Meant as a way to track what and how many servers this bot is in.
This list will not be available to the public.
No information about the people in the server are stored in this list, just the server name and ID number.
This is so that I can keep track of if I need to scale up resources for the bot to accomodate for extra use. 
Should the bot be in a larger number of servers, I will upscale resource allocations.
"""

from discord.ext import commands

class Tracker(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        with open("serverlist.txt", "a") as file:
            file.write(f"{guild.name}, {guild.id}\n")
            print(f"Joined `{guild.name}`! ({guild.id})")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        with open("serverlist.txt", "r") as file:
            lines = file.readlines()
        filtered = [line for line in lines if f"{guild.name}, {guild.id}" not in line]

        with open("serverlist.txt", "w") as file:
            file.writelines(filtered)
        
        print(f"Left `{guild.name}`! ({guild.id})")

async def setup(bot):
    await bot.add_cog(Tracker(bot))