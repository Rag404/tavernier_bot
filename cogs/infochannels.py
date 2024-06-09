from discord import Bot, Cog, Guild, Member, Status, VoiceChannel, VoiceState
from data.config import TAVERN_ID, MEMBERS_INFOCHANNEL, ONLINES_INFOCHANNEL
from discord.ext import tasks
from resources.utils import log

member_count = 0

class MemberCount(Cog):
    """Compte des membres sur le serveur"""

    def __init__(self, bot):
        self.bot: Bot = bot


    @Cog.listener()
    async def on_member_join(self, member: Member):
        """Increase the count"""

        if not member.bot:
            log(member, "just joined")
            await self.update()


    @Cog.listener()
    async def on_member_remove(self, member: Member):
        """Decrease the count"""

        if not member.bot:
            log(member, "has left")
            await self.update()


    @Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        """Kick members entering the channel"""

        if after.channel:
            if after.channel.id == MEMBERS_INFOCHANNEL:
                await member.move_to(before.channel)


    async def update(self):
        guild: Guild = self.bot.get_guild(TAVERN_ID)
        infochannel: VoiceChannel = self.bot.get_channel(MEMBERS_INFOCHANNEL)
        count = len([x for x in guild.members if not x.bot])

        await infochannel.edit(name=f"Membres : {count}")



class OnlineCount(Cog):
    """Compte des membres en ligne"""

    def __init__(self, bot):
        self.bot = bot


    global count_loop

    @tasks.loop(minutes=2)
    async def online_count_loop(self):
        guild: Guild = self.bot.get_guild(TAVERN_ID)
        channel: VoiceChannel = guild.get_channel(ONLINES_INFOCHANNEL)

        not_offlines = [member for member in guild.members if not member.bot and member.status != Status.offline]
        onlines = [member for member in not_offlines if member.status == Status.online]
        dnds = [member for member in not_offlines if member.status == Status.dnd]
        idles = [member for member in not_offlines if member.status == Status.idle]

        await channel.edit(name=f"🟢 {len(onlines)} ⛔ {len(dnds)} 🌙 {len(idles)}")


    @Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        """Kick members entering the channel"""

        if after.channel:
            if after.channel.id == ONLINES_INFOCHANNEL:
                await member.move_to(before.channel)


    @Cog.listener()
    async def on_ready(self):
        if not self.online_count_loop.is_running():
            self.online_count_loop.start()



def setup(bot):
    bot.add_cog(MemberCount(bot))
    print(" - Infochannels")
    print("    + MemberCount")
    bot.add_cog(OnlineCount(bot))
    print("    + OnlineCount")

def on_teardown(bot):
    OnlineCount.online_count_loop.cancel()
