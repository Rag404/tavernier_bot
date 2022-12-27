import traceback
from discord import ApplicationContext, Bot, Cog, Color, DiscordException, Embed, slash_command
from discord.ext.commands import NotOwner


class Test(Cog):
    def __init__(self, bot):
        self.bot: Bot = bot
    
    
    @Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        print("amogus")
    
    
    @slash_command(name="test")
    async def test_cmd(self, ctx):
        await ctx.respond("Amogus")


def setup(bot):
    bot.add_cog(Test(bot))
    print(" - Test")