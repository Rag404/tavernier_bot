from discord import Bot, Cog, Guild, Activity
from data.config import TAVERN_ID, ANIMES_PATH, MUSIC_GENRES_PATH, VIDEO_GAMES_PATH, MOVIES_PATH
from typing import List
from random import choice
from discord.ext import tasks
import asyncio


playing = 0
streaming = 1
listening = 2
watching = 3
competing = 5

def get_lines(path: str) -> List[str]:
    return open(path, encoding="utf-8").read().splitlines()

all_status = []
animes = get_lines(ANIMES_PATH)
music_genres = get_lines(MUSIC_GENRES_PATH)
video_games = get_lines(VIDEO_GAMES_PATH)
movies = get_lines(MOVIES_PATH)


class BotStatus(Cog):
    """Changement automatique du status"""
    
    def __init__(self, bot):
        self.bot: Bot = bot
    

    global status_loop

    @tasks.loop()
    async def status_loop(self):
        self.statusList()
        for activity in all_status:
            newActivity = Activity(type=activity[0], name=activity[1])
            await self.bot.change_presence(activity=newActivity)
            await asyncio.sleep(20)
    

    @Cog.listener()
    async def on_ready(self):
        status_loop.start(self)


    def statusList(self):
        global all_status

        guild: Guild = self.bot.get_guild(TAVERN_ID)
        members = [member for member in guild.members if not member.bot]

        # list of all looping status
        all_status = [
            [watching, f"{len(members)} membres"],
            [playing, choice(video_games)],
            [watching, choice(members).display_name],
            [watching, choice(animes)],
            [listening, choice(music_genres)],
            [watching, choice(movies)]
        ]


def setup(bot):
    bot.add_cog(BotStatus(bot))
    print(' - BotStatus')


def teardown(bot):
    status_loop.cancel()
    print('status cog unloaded')