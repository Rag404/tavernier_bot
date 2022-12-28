from discord import Cog, Bot, Member, VoiceState
from data.config import STREAK_WEEK_DAY, STREAK_HYPERACTIVE, HYPERACTIVE_ROLE, STREAK_TIME_MIN, REDIRECT_VOICE_CHANNEL, STREAK_DB_COLLECTION
from resources.database import database
from resources.utils import log
import datetime as dt
import pytz

col = database.get_collection(STREAK_DB_COLLECTION)


class MemberData:
    FIELDS = ("streak", "time", "last", "done")
    
    
    def __init__(self, member: Member, streak: int = 0, time: float = 0, last: float = 0, done: bool = False):
        self.member = member
        """The `discord.Member` object"""
        
        self.streak = streak
        """The member's week streak"""
        self.time = time
        """Hours spent in a voice channel for the current week"""
        self.last = last
        """The last time the member entered/left a voice channel (as timestamp)"""
        self.done = done
        """Whether or not the member has reached the weekly goal"""
        
        self.now = dt.datetime.now(pytz.timezone("CET"))
        """Time where the object was created"""
    
    
    def data(self):
        """Return data as a dict"""
        return {k: e for k, e in self.__dict__.items() if k in self.FIELDS}
    
    
    def commit(self):
        """Push member data into the database"""
        col.update_one({"_id": self.member.id}, {"$set": self.data()}, upsert=True)


    async def reset_progress(self):
        """Reset the streak of a member, and remove the hyperactive role from him if needed"""

        role = self.member.guild.get_role(HYPERACTIVE_ROLE)
        
        await self.member.remove_roles(role, reason=f"Lost a streak of {self.streak}")
        log(self.member, "lost a streak of", self.streak)
        
        self.streak = 0


    def expired(self) -> bool:
        """Check if a member has exceeded the time limit to increase his streak. Return False if the member is new"""

        if (timestamp := self.last) == 0:
            return False
        
        last_update = dt.datetime.fromtimestamp(timestamp)
        return streak_day(self.now) >= last_update


    def reached(self) -> bool:
        """Check if a member has reached the time needed to aquire the hyperactive role"""

        time = dt.timedelta(hours=self.time)
        return time >= STREAK_TIME_MIN


    async def update_time(self):
        """Add the time spent between now and the connection of a member to his progress"""

        last = dt.datetime.fromtimestamp(self.last)
        
        session = to_hours(self.now - last)
        self.time += session
        
        if self.done == False and self.reached():
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

        last = dt.datetime.fromtimestamp(self.last)
        day = streak_day(self.now)
        self.time += day - last
        
        if self.reached():
            await self.increase_streak()
        else:
            await self.reset_progress()
        
        self.time = to_hours(self.now - day)



def get_data(member: Member) -> MemberData:
    """Get a member's data from the database"""
    
    result = col.find_one({"_id": member.id}, {"_id": 0})
    return MemberData(member, **result)


def to_hours(delta: dt.timedelta) -> float:
    """Convert a timedelta object into a number of hours"""
    return delta / dt.timedelta(hours=1)


def streak_day(now: dt.date) -> dt.datetime:
    """Return a datetime object for the last weekly streak update relative to a given date"""

    days = abs(STREAK_WEEK_DAY - now.weekday())
    day = now - dt.timedelta(days=days)
    return dt.datetime.combine(day, dt.time())



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



def setup(bot: Bot):
    bot.add_cog(Hyperactive(bot))
    print(" - Hyperactive")