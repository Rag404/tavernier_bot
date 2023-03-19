from discord import Cog, Bot, Member, VoiceState, ApplicationContext, Embed, Color, slash_command, user_command, option
from data.config import HYPERACTIVE_DB_COLLECTION, HYPERACTIVE_WEEK_DAY, HYPERACTIVE_LEVELS, HYPERACTIVE_ROLES, REDIRECT_VOICE_CHANNEL, TAVERN_ID
from resources.database import database
from resources.utils import time2str
import datetime as dt


col = database.get_collection(HYPERACTIVE_DB_COLLECTION)


class MemberData:
    def __init__(self, member: Member, level: int = 0, time: float = 0, last: float = 0):
        self.member = member
        """The `discord.Member` object"""
        
        self.level = level
        """The hyperactive level the member has reached"""
        self.time = dt.timedelta(hours=time)
        """Hours spent in a voice channel for the current week"""
        self.last = dt.datetime.fromtimestamp(last)
        """The last time the member entered/left a voice channel (as timestamp)"""
        
        self.now = dt.datetime.utcnow()
        """Time when the object was created"""
    
    
    def commit(self):
        """Push member data into the database"""
        
        data = {
            "level": self.level,
            "time": self.time / dt.timedelta(hours=1),  # Convert into hours
            "last": self.last.timestamp()
        }
        col.update_one({"_id": self.member.id}, {"$set": data}, upsert=True)


    def expired(self) -> bool:
        """Check if a member has exceeded the time limit to increase his level. Return False if the member is new"""

        if self.last.timestamp() == 0:
            return False
        
        return streak_day(self.now) >= self.last


    def reached(self) -> bool:
        """Check if a member has the time needed to reach the next level"""
        
        return self.new_level() >= self.level + 1
    
    
    def new_level(self) -> int:
        """Returns the new level of the member based on his time and current level"""
        
        diff = streak_day(self.now) - self.last
        if diff > dt.timedelta(days=7):
            # If the member last connected more than a week ago, subtract the right amount of levels
            weeks = diff // dt.timedelta(days=7)
            return max(0, self.level - weeks)
        
        elif self.level+1 < len(HYPERACTIVE_LEVELS) and self.time >= HYPERACTIVE_LEVELS[self.level+1]:
            # If the time matches the requirement for the next level
            return self.level + 1
        
        elif self.level-1 >= 0 and self.time < HYPERACTIVE_LEVELS[self.level-1]:
            # If the time doesn't matches the requirement for the current level
            return self.level - 1
        
        else:
            return self.level
    
    
    def time_str(self) -> str:
        """Format member's time values into string"""
        
        if self.expired():
            return "0s"
        
        return time2str(self.time)
    
    
    async def update_time(self):
        """Add the time spent between now and the connection of a member to his progress"""

        self.time += self.now - self.last
        
        if self.reached():
            await self.update_role()
    
    
    async def update_role(self):
        new_role = self.member.guild.get_role(HYPERACTIVE_ROLES[self.new_level()])
        
        for role in self.member.roles:
            if role.id in HYPERACTIVE_ROLES:
                await self.member.remove_roles(role)
        
        await self.member.add_roles(new_role)


    async def handle_midnight(self):
        """Handle the case where a member connected before and left after midnight on reset day"""

        day = streak_day(self.now)
        self.time += day - self.last
        await self.update_role()
        
        self.time = self.now - day
        if self.reached():
            await self.update_role()



def get_data(member: Member) -> MemberData:
    """Get a member's data from the database"""
    
    result = col.find_one({"_id": member.id}, {"_id": 0}) or {}
    return MemberData(member, **result)


def streak_day(now: dt.date) -> dt.datetime:
    """Return a datetime object for the last weekly streak update relative to a given date"""

    days = abs(HYPERACTIVE_WEEK_DAY - now.weekday())
    day = now - dt.timedelta(days=days)
    full = dt.datetime.combine(day, dt.time())
    return full



class Hyperactive(Cog):
    """Rôle Hyperactif automatique"""
    
    def __init__(self, bot):
        self.bot: Bot = bot
    
    
    @Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        if member.bot or (before.channel and before.channel.id == REDIRECT_VOICE_CHANNEL):
            return
        
        memberdata = get_data(member)
        
        # When a channel is left
        if before.channel:
            if after.channel and before.channel == after.channel:
                return
            
            if memberdata.expired():
                await memberdata.handle_midnight()
            else:
                await memberdata.update_time()
        
        elif memberdata.expired():
            memberdata.level = memberdata.new_level()
            memberdata.time = dt.timedelta(0)
            await memberdata.update_role()
        
        memberdata.last = memberdata.now
        memberdata.commit()
    
    
    @slash_command(name="stats")
    @option("user", Member, description="Le membre à qui afficher les stats (vous-même par défaut)", required=False)
    async def stats_cmd(self, ctx: ApplicationContext, user: Member):
        """Montre tes statistiques, ou celles d'un autre membre"""
        
        await ctx.defer()
        
        data = get_data(user or ctx.author)
        member = data.member
        
        embed = Embed(
            title = f"Statistiques de {member}",
            color = Color.embed_background()
        )
        embed.set_thumbnail(url=member.avatar.url + "?size=1024")
        embed.add_field(
            name = "⏱️ Ancienneté",
            value = f"Compte créé le <t:{int(member.created_at.timestamp())}:D>\n" +
                    f"Serveur rejoint le <t:{int(member.joined_at.timestamp())}:D>"
        )
        embed.add_field(
            name = "⚡ Activité",
            value = f"**{data.time_str()}** en vocal cette semaine\n" +
                    f"**Niveau {max(data.level, data.new_level())}** d'hyperactivité",
            inline = False
        )
        
        await ctx.respond(embed=embed)
    
    
    @user_command(name="Statistiques")
    async def stats_user_cmd(self, ctx, user):
        await self.show_stats(ctx, user)



def setup(bot: Bot):
    bot.add_cog(Hyperactive(bot))
    print(" - Hyperactive")