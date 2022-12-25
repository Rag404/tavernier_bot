import json
from discord import Bot, CategoryChannel, Cog, Member, ActivityType, SlashCommandGroup, VoiceChannel, VoiceState, PermissionOverwrite, ApplicationContext, AllowedMentions, default_permissions, user_command, option
from data.config import REDIRECT_VOICE_CHANNEL, ROOMS_CATEGORY, ROOMS_SAVE_PATH, ROOM_LEADER_OVERWRITES
from discord.utils import get
from random import choice
from typing import Union
from my_utils import log


rooms = {}

def is_in_room(member: Member) -> bool:
    if member.voice:
        if member.voice.channel.id in rooms:
            return True
    return False


def is_cmd_in_room(ctx: ApplicationContext) -> bool:
    if ctx.channel_id in rooms:
        return True
    return False


def are_in_same_room(member_A: Member, member_B: Member):
    if is_in_room(member_A) and is_in_room(member_B):
        if member_A.voice.channel == member_B.voice.channel:
            return True
    return False


def is_room_leader(member: Member) -> bool:
    if is_in_room(member):
        if member.id == rooms[member.voice.channel.id]["leader"]:
            return True
    return False


def get_member_game_name(member: Member) -> Union[str, None]:
    for activity in member.activities:
        if activity.type == ActivityType.playing:
            return activity.name


async def rename_room_to_game(room: VoiceChannel, member: Member) -> Union[str, None]:
    game = get_member_game_name(member)
    if game and room.name != game:
        await room.edit(name=game, reason="Le chef de la room a changé de jeu")
    return game


class VoiceRoom(Cog):
    """Créer automatiquement des salons vocaux"""
    
    def __init__(self, bot):
        self.bot: Bot = bot
        self.bot.loop.create_task(self.handle_rooms(ctx=None))
    
    
    async def create_room(self, leader: Member) -> VoiceChannel:
        muted_role = get(leader.guild.roles, name="Muted")
        overwrites = {
            leader: ROOM_LEADER_OVERWRITES,
            muted_role: PermissionOverwrite(speak=False)
        }
        
        category = leader.guild.get_channel(ROOMS_CATEGORY)
        room_name = get_member_game_name(leader) or leader.display_name
        new_room = await leader.guild.create_voice_channel(name=room_name, category=category, overwrites=overwrites, reason=f"A créé une room")
        
        global rooms
        rooms[new_room.id] = {
            "leader": leader.id,
            "locked": False,
            "auto_name": True
        }
        
        await leader.move_to(new_room, reason="Téléporté dans une nouvelle room")
        await new_room.send(f"Le chef de la room est {leader.mention}", allowed_mentions=AllowedMentions.none())
        log(leader, f'has created the room "{new_room.name}"')
        
        new_room.members
        
        return new_room
    
    
    async def change_owner(self, room: VoiceChannel) -> Member:
        global rooms
        new_leader = room.members[0]
        rooms[room.id]["leader"] = new_leader.id
        
        await room.send(f"L'ancien leader a quitté, le nouveau leader est {new_leader.mention}")
        log(new_leader, f'is the new leader of the room "{room.name}"')
        return new_leader
    

    @Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        if after.channel is not None and after.channel.id == REDIRECT_VOICE_CHANNEL:
            # If the event is called by a member entering the redirect voice channel
            await self.create_room(member)
        
        if (room := before.channel) is not None and room.id in rooms and room != after.channel:
            # If the event was called by a member leaving a room
            if len([member for member in room.members if not member.bot]) == 0:
                # If the room is now empty (ignore bots)
                del rooms[room.id]
                await room.delete(reason="Room vide")
                log(f'The room "{room.name}" has been deserted')

            
            elif member.id == rooms[room.id]["leader"]:
                # If the member was the leader of its room
                await self.change_owner(room)
                await rename_room_to_game(room, member)


    @Cog.listener()
    async def on_presence_update(self, before: Member, after: Member):
        if before.id == self.bot.user.id:
            # If the event was called by the bot itself
            return
        
        if is_room_leader(after) and rooms[(room := after.voice.channel).id]["auto_name"] == True:
            # If the member who called this event is a room leader and if its room has auto-naming enabled
            old, new = room.name, await rename_room_to_game(room, after)
            if new:
                log(f'The room "{old}" has been auto-renamed to "{new}"')


    @Cog.listener()
    async def on_guild_channel_delete(self, channel: VoiceChannel):
        if channel.id not in rooms:
            return
        
        try:
            del rooms[channel.id]
            log(f'The room "{channel.name}" has been manually deleted')
        finally:
            pass


    room_commands = SlashCommandGroup("room", "Gérez votre room")
    

    @room_commands.command(name="rename")
    @option("name", description="Le nouveau nom de la room")
    async def rename_room(self, ctx: ApplicationContext, name: str):
        """Renommer la room"""
        
        if not is_room_leader(ctx.author):
            return await ctx.respond("Vous devez être dans une room et en être le leader pour pouvoir y autoriser quelqu'un !", ephemeral=True)
        
        room = ctx.author.voice.channel
        old_name = room.name
        await room.edit(name=name, reason=f"{ctx.author} a modifié le nom de la room")
        rooms[room.id]["auto_name"] = False
        
        log(ctx.author, f'has renamed the room "{old_name}" into "{name}"')
        await ctx.respond(f'Le nom de la room a été changé en "{name}"')


    @room_commands.command(name="auto-name")
    @option("state", description="On/Off", choices=["on", "off"])
    async def room_auto_name(self, ctx: ApplicationContext, state):
        """Changer automatiquement le nom de la room selon l'activité du leader"""
        
        if not is_room_leader(ctx.author):
            return await ctx.respond("Vous devez être dans une room et en être le leader pour pouvoir y autoriser quelqu'un !", ephemeral=True)
        
        room = ctx.author.voice.channel

        if state == "on":
            rooms[room.id]["auto_name"] = True
            log(ctx.author, f'has turned auto-name on in the room "{room.name}"')
            await ctx.respond("Le nom automatique de la room a été activé.")
        else:
            rooms[room.id]["auto_name"] = False
            log(ctx.author, f'has turned auto-name off in the room "{room.name}"')
            await ctx.respond("Le nom automatique de la room a été désactivé.")


    @room_commands.command(name="lock")
    async def lock_room(self, ctx: ApplicationContext):
        """Verrouiller la room pour que seul les membres présents y aient accès"""
        
        await ctx.defer()
        
        if not is_room_leader(ctx.author):
            return await ctx.respond("Vous devez être dans une room et en être le leader pour pouvoir y autoriser quelqu'un !", ephemeral=True)
        
        room = ctx.author.voice.channel
        
        for member in room.members:
            await room.set_permissions(member, connect=True)
        await room.set_permissions(ctx.guild.default_role, connect=False)
        
        rooms[room.id]["locked"] = True
        
        log(ctx.author, f'has locked the room "{room.name}"')
        await ctx.respond("La room a été verrouillée.")


    @room_commands.command(name="unlock")
    async def unlock_room(self, ctx: ApplicationContext):
        """Déverrouiller la room pour que tout le monde puisse y entrer"""
        
        await ctx.defer()
        
        if not is_room_leader(ctx.author):
            return await ctx.respond("Vous devez être dans une room et en être le leader pour pouvoir y autoriser quelqu'un !", ephemeral=True)
        
        room = ctx.author.voice.channel
        
        for item in room.overwrites:
            if type(item) is Member:
                await room.set_permissions(item, overwrite=None, reason=f"La room a été verrouillée par {ctx.author}")
        await room.set_permissions(ctx.guild.default_role, overwrite=None, reason=f"La room a été verrouillée par {ctx.author}")
        
        rooms[room.id]["locked"] = False
        
        log(ctx.author, f'has unlocked the room "{room.name}"')
        await ctx.respond("La room a été déverrouillée.")
    
    
    @room_commands.command(name="infos")
    async def room_infos(self, ctx: ApplicationContext):
        """Obtenir des informations sur la room"""
        
        if not is_in_room(ctx.author) and not is_cmd_in_room(ctx):
            return await ctx.respond("Vous devez être dans une room pour pouvoir en montrer les infos !", ephemeral=True)

        room = ctx.author.voice.channel
        room_data: dict = rooms[room.id]
        
        leader = ctx.guild.get_member(room_data["leader"])
        states = {True: "oui", False: "non"}
        locked, auto_name = room_data["locked"], room_data["auto_name"]
        
        await ctx.respond(f"Nom : {room.name} \nLeader : {leader.mention} \nVerrouillée : {states[locked]} \nNom automatique : {states[auto_name]}")


    @room_commands.command(name="blacklist")
    @option("member", description="Le membre à bannir de la room")
    async def blacklist_from_room(self, ctx: ApplicationContext, member: Member):
        """Empêche à un membre de rejoindre la room"""
        
        if not is_room_leader(ctx.author):
            return await ctx.respond("Vous devez être dans une room et en être le leader pour pouvoir y autoriser quelqu'un !", ephemeral=True)
        
        room = ctx.author.voice.channel
        await room.set_permissions(member, connect=False, reason="A été banni d'une room")
        
        if member.voice:
            if member.voice.channel.id == room.id:
                await member.move_to(None)
        
        log(ctx.author, "has blacklisted", member, f'in the room "{room.name}"')
        await ctx.respond(f"{member.mention} a été banni de la room.")


    @room_commands.command(name="whitelist")
    @option("member", description="Le membre à autoriser dans la room")
    async def whitelist_from_room(self, ctx: ApplicationContext, member: Member):
        """Autoriser un membre à rejoindre la room"""
        
        if not is_room_leader(ctx.author):
            await ctx.respond("Vous devez être dans une room et en être le leader pour pouvoir y autoriser quelqu'un !", ephemeral=True)
            return
        
        room = ctx.author.voice.channel
        await room.set_permissions(member, connect=True, reason="A été autorisé dans une room")

        log(ctx.author, "has whitelisted", member, f'in the room "{room.name}"')
        await ctx.respond(f"{member.mention} a été autorisé dans la room.")


    @room_commands.command(name="leader")
    @option("member", description="Le membre à définir comme leader")
    async def set_room_leader(self, ctx: ApplicationContext, member: Member):
        """Passer le lead de la room à un membre"""
        
        if not is_room_leader(ctx.author):
            return await ctx.respond("Vous devez être dans une room et en être le leader pour pouvoir en passer le lead !", ephemeral=True)
        if not are_in_same_room(ctx.author, member):
            return await ctx.respond("Ce membre n'est pas dans votre room !")
        
        room = ctx.author.voice.channel
        await room.set_permissions(member, overwrite=ROOM_LEADER_OVERWRITES)
        
        if rooms[room.id]["locked"]:
            await room.set_permissions(ctx.author, overwrite=PermissionOverwrite(connect=True))
        else:
            await room.set_permissions(ctx.author, overwrite=None)
        
        rooms[room.id]["leader"] = member.id
        
        if rooms[room.id]["auto_name"] and (game := get_member_game_name(member)) and room.name != game:
            await room.edit(name=game)
        
        log(member, f'is the new leader of the room "{room.name}"')
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
    
    
    @room_commands.command(name="handle")
    @default_permissions(administrator=True)
    async def handle_rooms(self, ctx: ApplicationContext):
        """Handle rooms which were created before the cog was loaded/reloaded"""
        
        await self.bot.wait_until_ready()
        
        print("Handling already existing rooms...")
        category: CategoryChannel = self.bot.get_channel(ROOMS_CATEGORY)
        
        save = {}
        with open(ROOMS_SAVE_PATH, encoding='utf-8') as file:
            save = json.load(file)
        
        unknown_rooms = [channel for channel in category.channels if channel.id not in rooms]
        
        for channel in unknown_rooms:
            if len(channel.members) == 0:
                await channel.delete(reason="Room vide")
                log(f'The room "{channel.name}" has been deleted')
            
            elif channel.id in save:
                rooms[channel.id] = save[channel.id]
            
            else:
                rooms[channel.id] = {
                    "leader": channel.members[0].id,
                    "locked": not channel.overwrites_for(category.guild.default_role).connect,
                    "auto_name": True
                }
                
        print("Rooms handling done")
        
        if ctx is not None:
            await ctx.respond("Rooms handling done", ephemeral=True)


def setup(bot: Bot):
    bot.add_cog(VoiceRoom(bot))
    print(" - VoiceRoom")


def teardown(bot):
    with open(ROOMS_SAVE_PATH, 'w') as file:
        json.dump(rooms, file, indent=2)