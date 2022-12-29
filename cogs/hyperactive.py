from discord import Cog, Bot, Member, VoiceState, ApplicationContext, Embed, Color, slash_command, user_command, option
from data.config import STREAK_WEEK_DAY, STREAK_HYPERACTIVE, HYPERACTIVE_ROLE, STREAK_TIME_MIN, REDIRECT_VOICE_CHANNEL, STREAK_DB_COLLECTION, TIMEZONE
from resources.database import database
from resources.utils import log
import datetime as dt

col = database.get_collection(STREAK_DB_COLLECTION)


class MemberData:
    def __init__(self, member: Member, streak: int = 0, time: float = 0, last: float = 0, done: bool = False):
        self.member = member
        """The `discord.Member` object"""
        
        self.streak = streak
        """The member's week streak"""
        self.time = dt.timedelta(hours=time)
        """Hours spent in a voice channel for the current week"""
        self.last = TIMEZONE.localize(dt.datetime.fromtimestamp(last))
        """The last time the member entered/left a voice channel (as timestamp)"""
        self.done = done
        """Whether or not the member has reached the weekly goal"""
        
        self.now = dt.datetime.now(TIMEZONE)
        """Time when the object was created"""
    
    
    def commit(self):
        """Push member data into the database"""
        
        data = {
            "streak": self.streak,
            "time": self.time / dt.timedelta(hours=1),  # Convert into hours
            "last": self.last.timestamp(),
            "done": self.done
        }
        col.update_one({"_id": self.member.id}, {"$set": data}, upsert=True)


    async def reset_progress(self):
        """Reset the streak of a member, and remove the hyperactive role from him if needed"""

        role = self.member.guild.get_role(HYPERACTIVE_ROLE)
        
        await self.member.remove_roles(role, reason=f"Lost a streak of {self.streak}")
        log(self.member, "lost a streak of", self.streak)
        
        self.streak = 0


    def expired(self) -> bool:
        """Check if a member has exceeded the time limit to increase his streak. Return False if the member is new"""

        if self.last == dt.datetime(1970, 1, 1):
            return False
        
        return streak_day(self.now) >= self.last


    def reached(self) -> bool:
        """Check if a member has reached the time needed to aquire the hyperactive role"""

        return self.time >= STREAK_TIME_MIN


    async def update_time(self):
        """Add the time spent between now and the connection of a member to his progress"""

        self.time += self.now - self.last
        
        if not self.done and self.reached():
            self.done = True
            await self.increase_streak()


    async def increase_streak(self):
        """Increase the streak of a member and give him the hyperactive role if needed"""

        if self.streak < STREAK_HYPERACTIVE <= self.streak + 1:
            role = self.member.guild.get_role(HYPERACTIVE_ROLE)
            await self.member.add_roles(role)
            log(self.member, "got the hyperactive role")
        
        self.streak += 1


    async def handle_midnight(self):
        """Handle the case where a member connected before and left after midnight on reset day"""

        day = streak_day(self.now)
        self.time += day - self.last
        
        if self.reached():
            await self.increase_streak()
        else:
            await self.reset_progress()
        
        self.time = self.now - day



def get_data(member: Member) -> MemberData:
    """Get a member's data from the database"""
    
    result = col.find_one({"_id": member.id}, {"_id": 0}) or {}
    return MemberData(member, **result)


def streak_day(now: dt.date) -> dt.datetime:
    """Return a datetime object for the last weekly streak update relative to a given date"""

    days = abs(STREAK_WEEK_DAY - now.weekday())
    day = now - dt.timedelta(days=days)
    full = dt.datetime.combine(day, dt.time())
    return TIMEZONE.localize(full)


def timedelta_str(td: dt.timedelta) -> str:
    """Format timedelta values into string"""
    
    values = {}
    values["j"], r = divmod(td.seconds, 86400)
    values["h"], r = divmod(r, 3600)
    values["min"], values["s"] = divmod(r, 60)
    
    return " ".join([str(v) + k for k, v in values.items() if v > 0]) or "0s"



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
            memberdata.done = False
        
        memberdata.last = memberdata.now
        memberdata.commit()
    
    
    @slash_command(name="stats")
    @option("user", Member, description="Le membre à qui afficher les stats (vous-même par défaut)", required=False)
    async def show_stats(self, ctx: ApplicationContext, user: Member):
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
            value = f"**{timedelta_str(data.time)}** en vocal cette semaine\n" +
                    f"**{data.streak} semaine{'s' if data.streak > 1 else ''}** d'hyperactivité",
            inline = False
        )
        
        await ctx.respond(embed=embed)
    
    
    @user_command(name="Statistiques")
    async def show_stats_user(self, ctx, user):
        await self.show_stats(ctx, user)



def setup(bot: Bot):
    bot.add_cog(Hyperactive(bot))
    print(" - Hyperactive")