from discord import Cog, Bot, Member, VoiceState, ApplicationContext, Embed, Color, slash_command, user_command, option, default_permissions
from discord.ext.tasks import loop
from data.config import HYPERACTIVE_DB_COLLECTION, HYPERACTIVE_WEEK_DAY, HYPERACTIVE_LEVELS, HYPERACTIVE_ROLES, REDIRECT_VOICE_CHANNEL, LEADERBOARD_CHANNEL, LEADERBOARD_LIMIT, CONSOLE_CHANNEL
from resources.database import database
from resources.utils import time2str, wait_until
import datetime as dt
import json


col = database.get_collection(HYPERACTIVE_DB_COLLECTION)


class BaseMemberData:
    def __init__(self, member_id: int, level: int = 0, time: float = 0, last: float = 0):
        self.member_id = member_id
        """The ID of the discord member"""
        self.level = level
        """The hyperactive level the member has reached"""
        self.time = dt.timedelta(hours=time)
        """Hours spent in a voice channel for the current week"""
        self.last = dt.datetime.fromtimestamp(last)
        """The last time the member entered/left a voice channel (as timestamp)"""
        
        self.now = dt.datetime.utcnow()
        """Time when the object was created"""
    
    
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
    
    
    def display_level(self) -> int:
        """Return the display display level, which is the higher value between `self.level` and `self.new_level()`"""
        
        return max(self.level, self.new_level())
    
    
    def time_str(self) -> str:
        """Format member's time values into string"""
        
        if self.expired():
            return "0s"
        
        return time2str(self.time)
    
    
    def update_time(self):
        """Add the time spent between now and the connection of a member to his progress"""

        self.time += self.now - self.last



class MemberData(BaseMemberData):
    def __init__(self, member: Member, level: int = 0, time: float = 0, last: float = 0):
        super().__init__(member.id, level, time, last)
        
        self.member = member
        """The `discord.Member` object"""
    
    
    def commit(self):
        """Push member data into the database"""
        
        data = {
            "level": self.level,
            "time": self.time / dt.timedelta(hours=1),  # Convert into hours
            "last": self.last.timestamp()
        }
        col.update_one({"_id": self.member.id}, {"$set": data}, upsert=True)

    
    async def update_role(self):
        new_role = self.member.guild.get_role(HYPERACTIVE_ROLES[self.display_level()])
        
        for role in self.member.roles:
            if role.id in HYPERACTIVE_ROLES:
                await self.member.remove_roles(role)
        
        if new_role:
            await self.member.add_roles(new_role)


    async def handle_midnight(self):
        """Handle the case where a member connected before and left after midnight on reset day"""

        day = streak_day(self.now)
        self.time += day - self.last
        await self.update_role()
        
        self.time = self.now - day
        if self.reached():
            await self.update_role()



# - - - - - - - - - - - Hyperactive Roles - - - - - - - - - - -



def get_data(member: Member) -> MemberData:
    """Get a member's data from the database"""
    
    result = col.find_one({"_id": member.id}, {"_id": 0}) or {}
    return MemberData(member, **result)


def streak_day(now: dt.date = None) -> dt.datetime:
    """Return a datetime object for the last weekly streak update relative to a given date"""
    
    days = abs(HYPERACTIVE_WEEK_DAY - now.weekday())
    day = now - dt.timedelta(days=days)
    full = dt.datetime.combine(day, dt.time())
    return full


def false_alert(member: Member, before: VoiceState, after: VoiceState) -> bool:
    """Return if an `on_voice_state_update` event has been triggered in unwanted circumstances"""
    
    checks = [
        # If the member is a bot
        member.bot,
        # If the left and joined channel are both None
        not before.channel and not after.channel,
        # If the channel left is the redirect voice channel
        getattr(before.channel, "id", None) == REDIRECT_VOICE_CHANNEL,
        # If the channel left is the same as the channel joined
        before.channel == after.channel
    ]
    
    # If any of the checks passes, then it is a false alert
    if any(checks):
        return True
    else:
        return False



class Hyperactive(Cog):
    """Rôle Hyperactif automatique"""
    
    def __init__(self, bot):
        self.bot: Bot = bot
    
    
    @Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        if false_alert(member, before, after):
            return
        
        member_data = get_data(member)
        
        # When a channel is left
        if before.channel and before.channel != after.channel:
            if member_data.expired():
                # Handle the case where a member connected before and left after midnight on reset day
                await member_data.handle_midnight()
            else:
                member_data.update_time()
                
            if member_data.reached():
                await member_data.update_role()
        
        # Or if the member last connected last week
        elif member_data.expired():
            member_data.level = member_data.new_level()
            member_data.time = dt.timedelta(0)
            await member_data.update_role()
        
        member_data.last = member_data.now
        member_data.commit()
    
    
    @slash_command(name="stats")
    @option("user", Member, description="Le membre à qui afficher les stats (vous-même par défaut)", required=False)
    async def stats_cmd(self, ctx: ApplicationContext, user: Member):
        """Montre tes statistiques, ou celles d'un autre membre"""
        
        await ctx.defer()
        
        data = get_data(user or ctx.author)
        member = data.member
        
        embed = Embed(
            title = f"Statistiques de @{member.name}",
            color = Color.embed_background()
        )
        
        embed.add_field(
            name = "⏱️ Ancienneté",
            value = f"Compte créé le <t:{int(member.created_at.timestamp())}:D>\n" +
                    f"Serveur rejoint le <t:{int(member.joined_at.timestamp())}:D>"
        )
        embed.add_field(
            name = "⚡ Activité",
            value = f"**{data.time_str()}** en vocal cette semaine\n" +
                    f"**Niveau {data.display_level()}** d'hyperactivité",
            inline = False
        )
        
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url + "?size=1024")
        else:
            embed.set_thumbnail(url=member.default_avatar)
        
        await ctx.respond(embed=embed)
    
    
    @user_command(name="Statistiques")
    async def stats_user_cmd(self, ctx, user):
        await self.stats_cmd(ctx, user)



# - - - - - - - - - - - Leaderboard - - - - - - - - - - -


def get_rankings() -> list[list[BaseMemberData]]:
    rankings: list[list[BaseMemberData]] = []
    
    for result in col.find():
        id = result.pop("_id")
        member_data = BaseMemberData(id, **result)
        
        if member_data.time == 0 or (streak_day(member_data.now) - member_data.last) > dt.timedelta(weeks=1):
            continue
        
        for i, rank in enumerate(rankings):
            if member_data.time == rank[0].time:
                rankings[i].append(member_data)
                break
            elif member_data.time > rank[0].time:
                rankings.insert(i, [member_data])
                break
        else:
            rankings.append([member_data])
    
    return rankings


def rank_emoji(rank: int) -> str:
    if rank == 1:
        return "🏆"
    elif rank == 2:
        return "🥈"
    elif rank == 3:
        return "🥉"
    else:
        return "#" + str(rank)


def level_str(level: int) -> str:
    if level == 0:
        return ""
    elif level == 1:
        return "| niveau Ⅰ"
    elif level == 2:
        return "| niveau Ⅱ"
    elif level == 3:
        return "| niveau Ⅲ"
    elif level == 4:
        return "| niveau Ⅳ"
    else:
        return "| niveau Ⅴ"


def leaderboard_embed(rank_limit: int) -> Embed:
    """Return a Discord embed with the hyperactive leaderboard of the server"""
    
    rankings_list = get_rankings()
    embed = Embed(
        title = "Classement d'activité",
        description = "Voici les membres les plus actifs en vocal sur la Taverne cette semaine.\nPetit rappel : pensez à vous hydrater et à toucher de l'herbe ;)\n\n",
        color = Color.gold()
    )
    
    for i, rank in enumerate(rankings_list):
        if i >= rank_limit:
            break
        
        for member_data in rank:
            prefix = rank_emoji(i+1)
            mention = "<@" + str(member_data.member_id) + ">"
            level = level_str(member_data.level)
            time = time2str(member_data.time)
            embed.description += f"{prefix} - {mention} | **{time}** {level}\n"
    
    return embed



class Leaderboard(Cog):
    """Classement des membres les plus actifs"""
    
    def __init__(self, bot):
        self.bot: Bot = bot
    
    
    async def send_leaderboard(self):
        channel = self.bot.get_channel(LEADERBOARD_CHANNEL)
        embed = leaderboard_embed(LEADERBOARD_LIMIT)
        await channel.send(embed=embed)
    

    @loop()
    async def leaderboard_loop(self):
        now = dt.datetime.now()
        next = streak_day(now) + dt.timedelta(weeks=1, seconds=1)
        await wait_until(next)
        
        await self.send_leaderboard()
    
    
    @Cog.listener()
    async def on_ready(self):
        self.leaderboard_loop.start()
    
    
    @slash_command(name="leaderboard")
    @default_permissions(administrator=True)
    @option("rank_limit", description="Nombre maximal de rangs à afficher (10 par défaut)", min_value=1)
    async def leaderboard_cmd(self, ctx: ApplicationContext, rank_limit: int = 10):
        """Affiche le classement des membres les plus actifs"""
        
        embed = leaderboard_embed(rank_limit)
        await ctx.respond(embed=embed)



def setup(bot: Bot):
    bot.add_cog(Hyperactive(bot))
    print(" - Hyperactive")
    bot.add_cog(Leaderboard(bot))
    print("    + Leaderboard")