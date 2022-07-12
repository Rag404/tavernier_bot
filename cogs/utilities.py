from discord import Bot, Cog, Member, ApplicationContext, VoiceState, option, slash_command


afk_list = {}


class Utilities(Cog):
    """Commandes utilitaires"""
    
    def __init__(self, bot):
        self.bot: Bot = bot
    
    
    async def rename(self, member: Member, new_nick: str, reason: str = None) -> None:
        if new_nick != member.nick:
            if new_nick == member.name:
                await member.edit(nick=None, reason=reason)
            else:
                await member.edit(nick=new_nick, reason=reason)
    
    
    @slash_command(name="afk")
    @option("time", min_value=1, max_value=60)
    @option("unit", choices=["secondes", "minutes", "heures"])
    async def afk(self, ctx: ApplicationContext, time: int, unit: str):
        """Change votre pseudo pour indiquer que vous êtes AFK"""
        
        global afk_list
        
        if ctx.author.voice is None:
            await ctx.respond("Vous devez être dans un salon vocal pour effectuer cette commande !", ephemeral=True)
            return
        
        units = {
            "secondes": "sec",
            "minutes": "min",
            "heures": "h"
        }
        
        id = ctx.author.id
        last_nick = ctx.author.display_name
        new_nick = f"[AFK {time}{units[unit]}] "
        
        if id in afk_list:
            new_nick += afk_list[id]
        else:
            new_nick += last_nick
        
        afk_list[id] = last_nick

        await self.rename(ctx.author, new_nick, "A effectué la commande /reviens-dans")
        await ctx.respond("vous etes AFK", ephemeral=True)


    @Cog.listener()
    async def on_member_update(self, before: Member, after: Member):
        if before.id in afk_list and after.nick:
            if not after.nick.startswith("[AFK ") and before.nick != after.nick:
                afk_list.pop(before.id)


    @Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        global afk_list
        if member.id in afk_list:
            new_nick = afk_list[member.id]
            
            if before and not after:
                await self.rename(member, new_nick, "N'est plus AFK")
                afk_list.pop(member.id)

            elif before and after:
                if before.self_mute and not after.self_mute:
                    await self.rename(member, new_nick, "N'est plus AFK")
                    afk_list.pop(member.id)


def setup(bot):
    bot.add_cog(Utilities(bot))
    print(' - Utilities')