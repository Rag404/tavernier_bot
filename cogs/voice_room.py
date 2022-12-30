from discord import Bot, CategoryChannel, Cog, Member, ActivityType, SlashCommandGroup, VoiceChannel, VoiceState, PermissionOverwrite, ApplicationContext, AllowedMentions, default_permissions, user_command, option
from data.config import REDIRECT_VOICE_CHANNEL, ROOMS_CATEGORY, ROOMS_DB_COLLECTION, ROOM_LEADER_OVERWRITES, BOT_ROLE
from discord.utils import get
from typing import Optional
from resources.utils import log
from resources.database import database


col = database.get_collection(ROOMS_DB_COLLECTION)


class Room:
    def __init__(self, channel: VoiceChannel, leader: Member, locked: bool = False, auto_name: bool = True) -> None:
        self.channel = channel
        """The dicord.VoiceChannel object"""
        
        self.leader = leader
        """The leader of the room"""
        self.locked = locked
        """Whether or not the room is locked to other members"""
        self.auto_name = auto_name
        """Whether or not the room's name is synchronized with the leader's activity"""

    
    def commit(self):
        """Push room data into the database"""
        
        data = {
            "leader": self.leader.id,
            "locked": self.locked,
            "auto_name": self.auto_name
        }
        return col.update_one({"_id": self.channel.id}, {"$set": data}, upsert=True)
    
    
    async def delete(self, reason: str = None):
        """Delete the room"""
        
        await self.channel.delete(reason=reason)
        return col.delete_one({"_id": self.channel.id})
    
    
    def members(self) -> list[Member]:
        """Get a list of members in the room, excluding bots"""
        return [m for m in self.channel.members if not m.bot]
    
    
    def empty(self) -> bool:
        """Check if the room is empty of members (ignore bots)"""
        return len(self.members()) == 0

    
    async def rename_to_game(self, member: Member) -> Optional[str]:
        """Change the room's name to a member's game name, no changes if the member is not playing"""
        
        game = game_name(member)
        if game and self.channel.name != game:
            await self.channel.edit(name=game, reason="Le chef de la room a changé de jeu")
        return game


    def change_leader(self) -> Member:
        """Change leader to the first member to have joined the room"""
        
        self.leader = self.members()[0]
        log(self.leader, f'is the new leader of the room "{self.channel.name}"')
        return self.leader



def get_room(channel: VoiceChannel) -> Optional[Room]:
    """Get a room's data by its id, `None` if not found"""
    
    result = col.find_one({"_id": channel.id}, {"_id": 0})
    
    if result:
        result["leader"] = channel.guild.get_member(result.get("leader"))
        return Room(channel, **result)


def get_member_room(member: Member) -> Optional[Room]:
    """Get the room where a member is connected, `None` if not found"""
    
    if member.voice and member.voice.channel:
        return get_room(member.voice.channel)


def is_in_room(member: Member) -> bool:
    return member.voice and member.voice.channel.category and member.voice.channel.category.id == ROOMS_CATEGORY
    

def in_same_room(member_A: Member, member_B: Member):
    if is_in_room(member_A) and is_in_room(member_B):
        return member_A.voice.channel == member_B.voice.channel
    return False


def game_name(member: Member) -> Optional[str]:
    for activity in member.activities:
        if activity.type == ActivityType.playing:
            return activity.name


async def create_room(leader: Member) -> Room:
    bot_role = get(leader.guild.roles, id=BOT_ROLE)
    muted_role = get(leader.guild.roles, name="Muted")
    overwrites = {
        leader: ROOM_LEADER_OVERWRITES,
        bot_role: PermissionOverwrite(connect=True),
        muted_role: PermissionOverwrite(speak=False)
    }
    
    category = leader.guild.get_channel(ROOMS_CATEGORY)
    room_name = game_name(leader) or leader.display_name
    channel = await category.create_voice_channel(name=room_name, overwrites=overwrites, reason=f"A créé une room")
    
    await leader.move_to(channel, reason="Téléporté dans une nouvelle room")
    await channel.send(f"Le chef de la room est {leader.mention}", allowed_mentions=AllowedMentions.none())
    log(leader, f'has created the room "{channel.name}"')
    
    room = Room(channel, leader)
    room.commit()
    return room



class VoiceRoom(Cog):
    """Créer automatiquement des salons vocaux"""
    
    def __init__(self, bot):
        self.bot: Bot = bot
        self.bot.loop.create_task(self.handle_rooms())
    

    @Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        if after.channel:
            if after.channel.id == REDIRECT_VOICE_CHANNEL:
                room = await create_room(member)
        
        if before.channel != after.channel and (room := get_room(before.channel)):
            if room.empty():
                await room.delete(reason="Room vide")
                log(f'The room "{room.channel.name}" has been deserted')
            
            elif member == room.leader:
                new_leader = room.change_leader()
                await room.channel.send(f"L'ancien leader a quitté, le nouveau leader est {new_leader.mention}")
                await room.rename_to_game(new_leader)


    @Cog.listener()
    async def on_presence_update(self, before: Member, after: Member):
        if before.id == self.bot.user.id:
            return  # If the event was called by the bot itself
        
        if (room := get_member_room(after)) and room.auto_name:
            # If the member who called this event is a room leader and if its room has auto-naming enabled
            old = room.channel.name
            if new := await room.rename_to_game(after):
                log(f'The room "{old}" has been auto-renamed to "{new}"')


    @Cog.listener()
    async def on_guild_channel_delete(self, channel: VoiceChannel):
        if channel.category and channel.category.id != ROOMS_CATEGORY:
            return
        
        try:
            await get_room(channel).delete()
            log(f'The room "{channel.name}" has been manually deleted')
        except:
            pass


    room_commands = SlashCommandGroup("room", "Gérez votre room")
    

    @room_commands.command(name="rename")
    @option("name", description="Le nouveau nom de la room")
    async def rename_room(self, ctx: ApplicationContext, name: str):
        """Renommer la room"""
        
        room = get_member_room(ctx.author)
        
        if not room or ctx.author != room.leader:
            return await ctx.respond("Vous devez être dans une room et en être le leader pour pouvoir en changer les paramètres !", ephemeral=True)
        
        old_name = room.channel.name
        await room.channel.edit(name=name, reason=f"{ctx.author} a modifié le nom de la room")
        
        room.auto_name = False
        room.commit()
        
        log(ctx.author, f'has renamed the room "{old_name}" into "{name}"')
        await ctx.respond(f'Le nom de la room a été changé en "{name}"')


    @room_commands.command(name="auto-name")
    @option("state", description="On/Off", choices=["on", "off"])
    async def room_auto_name(self, ctx: ApplicationContext, state):
        """Déterminer si la room change automatiquement de nom lorsque le leader change son jeu"""
        
        room = get_member_room(ctx.author)
        
        if not room or ctx.author != room.leader:
            return await ctx.respond("Vous devez être dans une room et en être le leader pour pouvoir en changer les paramètres !", ephemeral=True)

        if state == "on" and room.auto_name == False:
            room.auto_name = True
            room.commit()
            log(ctx.author, f'has turned auto-name on in the room "{room.channel.name}"')
            await ctx.respond("Le nom automatique de la room a été activé.")
        
        elif state == "off" and room.auto_name == True:
            room.auto_name = False
            room.commit()
            log(ctx.author, f'has turned auto-name off in the room "{room.channel.name}"')
            await ctx.respond("Le nom automatique de la room a été désactivé.")
        
        else:
            await ctx.respond(f"Le nom automatique était déjà sur `{state}`")


    
    async def lock_cmd(self, ctx: ApplicationContext, locked: bool):
        await ctx.defer()
        room = get_member_room(ctx.author)
        state = "verrouillée" if locked else "déverrouillée"
        
        if not room or ctx.author != room.leader:
            return await ctx.respond("Vous devez être dans une room et en être le leader pour pouvoir en changer les paramètres !", ephemeral=True)
        
        if room.locked == locked:
            return await ctx.respond(f"La room est déjà {state}")
        
        for member in room.members():
            await room.channel.set_permissions(member, connect=locked, reason=f"La room a été {state} par {ctx.author}")
        await room.channel.set_permissions(ctx.guild.default_role, connect=(not locked), reason=f"La room a été {state} par {ctx.author}")
        
        room.locked = locked
        room.commit()
        
        log(ctx.author, f'has {"locked" if locked else "unlocked"} the room "{room.channel.name}"')
        await ctx.respond("La room a été verrouillée.")


    @room_commands.command(name="lock")
    async def lock_room(self, ctx):
        """Verrouiller la room pour que seul les membres présents y aient accès"""
        await self.lock_cmd(ctx, True)


    @room_commands.command(name="unlock")
    async def unlock_room(self, ctx):
        """Déverrouiller la room pour que tout le monde puisse y entrer"""
        await self.lock_cmd(ctx, False)
    
    
    
    @room_commands.command(name="infos")
    async def room_infos(self, ctx: ApplicationContext):
        """Obtenir des informations sur la room"""
        
        room = get_member_room(ctx.author)
        
        if not room or ctx.channel != room.channel:
            return await ctx.respond("Vous devez être dans une room pour pouvoir en montrer les infos !", ephemeral=True)
        
        STATES = {True: "\\✅", False: "\\❌"}
        await ctx.respond(
            f"Nom : {room.channel.name} \nLeader : {room.leader.mention} \nVerrouillée : {STATES[room.locked]} \nNom automatique : {STATES[room.auto_name]}",
            allowed_mentions = AllowedMentions(users=False)
        )


    @room_commands.command(name="blacklist")
    @option("member", description="Le membre à bannir de la room")
    async def blacklist_from_room(self, ctx: ApplicationContext, member: Member):
        """Empêche à un membre de rejoindre la room"""
        
        room = get_member_room(ctx.author)
        
        if not room or ctx.author != room.leader:
            return await ctx.respond("Vous devez être dans une room et en être le leader pour pouvoir en changer les paramètres !", ephemeral=True)
        
        if member == ctx.author:
            return await ctx.respond("Vous ne pouvez pas vous bannir vous-même !", ephemeral=True)
        
        await room.channel.set_permissions(member, connect=False, send_messages=False, reason="A été banni d'une room")
        
        if member.voice and member.voice.channel.id == room.channel.id:
            await member.move_to(None)
        
        log(ctx.author, "has blacklisted", member, f'in the room "{room.channel.name}"')
        await ctx.respond(f"{member.mention} a été banni de la room.")


    @room_commands.command(name="whitelist")
    @option("member", description="Le membre à autoriser dans la room")
    async def whitelist_from_room(self, ctx: ApplicationContext, member: Member):
        """Autoriser un membre à rejoindre la room"""
        
        room = get_member_room(ctx.author)
        
        if not room or ctx.author != room.leader:
            return await ctx.respond("Vous devez être dans une room et en être le leader pour pouvoir en changer les paramètres !", ephemeral=True)
        
        await room.channel.set_permissions(member, connect=True, send_messages=True, reason="A été autorisé dans une room")

        log(ctx.author, "has whitelisted", member, f'in the room "{room.channel.name}"')
        await ctx.respond(f"{member.mention} a été autorisé dans la room.")


    @room_commands.command(name="leader")
    @option("member", description="Le membre à définir comme leader")
    async def set_room_leader(self, ctx: ApplicationContext, member: Member):
        """Passer le lead de la room à un membre"""
        
        room = get_member_room(ctx.author)
        
        if not room or ctx.author != room.leader:
            return await ctx.respond("Vous devez être dans une room et en être le leader pour pouvoir en changer les paramètres !", ephemeral=True)
        if not in_same_room(ctx.author, member):
            return await ctx.respond("Ce membre n'est pas dans votre room !", ephemeral=True)
        
        if room.locked:
            await room.channel.set_permissions(ctx.author, connect=True)
        else:
            await room.channel.set_permissions(ctx.author, overwrite=None)
        
        await room.channel.set_permissions(member, overwrite=ROOM_LEADER_OVERWRITES)
        room.leader = member
        room.commit()
        
        if room.auto_name:
            await room.rename_to_game(member)
        
        log(member, f'is the new leader of the room "{room.channel.name}"')
        await ctx.respond(f"{member.mention} est le nouveau leader de la room.")


    @user_command(name="Room: Blacklist")
    async def blacklist_user_command(self, ctx, user):
        await self.blacklist_from_room(ctx, user)
        
    @user_command(name="Room: Whitelist")
    async def whitelist_user_command(self, ctx, user):
        await self.whitelist_from_room(ctx, user)

    @user_command(name="Room: Leader")
    async def leader_user_command(self, ctx, user):
        await self.set_room_leader(ctx, user)
    
    
    async def handle_rooms(self):
        await self.bot.wait_until_ready()
        
        print("Handling deleted rooms...")
        category: CategoryChannel = self.bot.get_channel(ROOMS_CATEGORY)
        
        room_ids = col.find({}, ["_id"])
        unknown_rooms = [channel for channel in category.channels if channel.id not in room_ids]
        to_delete = []
        
        for channel in unknown_rooms:
            if len([m for m in channel.members if not m.bot]) == 0:
                to_delete.append(channel.id)
                await channel.delete(reason="Room vide")
        
        if to_delete:
            col.delete_many({"_id": {"$in": to_delete}})
    
    
    @room_commands.command(name="handle")
    @default_permissions(administrator=True)
    async def handle_cmd(self, ctx: ApplicationContext):
        """Handle rooms which were created before the cog was loaded/reloaded"""
        
        await self.handle_rooms()
        log("Rooms handling done")
        await ctx.respond("Rooms handling done")


def setup(bot: Bot):
    bot.add_cog(VoiceRoom(bot))
    print(" - VoiceRoom")