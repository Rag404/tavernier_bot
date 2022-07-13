from discord import Bot, Cog, Member, Game, ActivityType, SlashCommandGroup, VoiceChannel, VoiceState, PermissionOverwrite, ApplicationContext, user_command, option
from discord.utils import get
from random import choice
from typing import Union
from my_utils import log


redirect_voice_channel = 996160558371979355
rooms_category = 996159603324768276
rooms = {}


class VoiceRoom(Cog):
    """Créer automatiquement des salons vocaux"""
    
    def __init__(self, bot):
        self.bot: Bot = bot


    def is_room_leader(self, member: Member) -> bool:
        if member.voice:
            if member.voice.channel.id in rooms:
                room = member.voice.channel
                if member.id == rooms[room.id]["leader"]:
                    return True
        return False

    def get_member_game_name(self, member: Member) -> Union[Game, None]:
        for activity in member.activities:
            if activity.type == ActivityType.playing:
                return activity.name

    async def rename_room_to_game(self, room: VoiceChannel, member: Member) -> None:
        if game := self.get_member_game_name(member):
            if room.name != game:
                await room.edit(name=game, reason="Le chef de la room a changé de jeu")
            return


    @Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        if after.channel:
            if after.channel.id == redirect_voice_channel:
                muted_role = get(member.guild.roles, name="Muted")
                overwrites = {
                    member: PermissionOverwrite(manage_channels=True, manage_permissions=True, move_members=True, mute_members=True, deafen_members=True, manage_events=True),
                    muted_role: PermissionOverwrite(speak=False)
                }
                
                category = member.guild.get_channel(rooms_category)
                room_name = self.get_member_game_name(member) or member.display_name
                new_room = await member.guild.create_voice_channel(name=room_name, category=category, overwrites=overwrites, reason=f"A créé une room")
                
                rooms[new_room.id] = {
                    "leader": member.id,
                    "locked": False,
                    "auto_name": True
                }
                
                await member.move_to(new_room, reason="Téléporté dans une nouvelle room")
                log(member, f'has created the room "{new_room.name}"')
        
        elif before.channel:
            if before.channel.id in rooms:
                room = before.channel
                if len(room.members) == 0:
                    await room.delete(reason="Gaming room vide")
                    log(f'The room "{room.name}" has been deleted')
                elif self.is_room_leader(member.id):
                    new_leader = choice(room.members)
                    rooms[room.id]["leader"] = new_leader.id
                    log(new_leader, f'is the new leader of the room "{room.name}"')


    @Cog.listener()
    async def on_presence_update(self, before: Member, after: Member):
        if before.id == self.bot.user.id:
            return
        
        if self.is_room_leader(after):
            room = after.voice.channel
            if rooms[room.id]["auto_name"] == True:
                old_name = room.name
                await self.rename_room_to_game(room, after)
                log(f'The room "{old_name}" has been auto-renamed to "{room.name}"')


    @Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if channel.id in rooms:
            del rooms[channel.id]


    room_commands = SlashCommandGroup("room", "Gérez votre room")


    @room_commands.command(name="rename")
    @option("name", description="Le nouveau nom de la room")
    async def rename_room(self, ctx: ApplicationContext, name: str):
        """Renommer la room"""
        
        if not ctx.author.voice:
            await ctx.respond("Vous devez être dans une room et en être le leader pour pouvoir en changer le nom !", ephemeral=True)
            return
        channel = ctx.author.voice.channel
        if not channel.id in rooms:
            await ctx.respond("Vous devez être dans une room et en être le leader pour pouvoir en changer le nom !", ephemeral=True)
            return
        if ctx.author.id != rooms[channel.id]["leader"]:
            await ctx.respond("Vous devez être le leader de la room pour pouvoir changer le nom !", ephemeral=True)
            return
        
        await channel.edit(name=name, reason=f"{ctx.author} a modifié le nom de la room")
        log(ctx.author, f'has renamed the room "{channel.name}" into "{name}"')
        await ctx.respond(f'Le nom de la room a été changé en "{name}"')


    @room_commands.command(name="auto-name")
    @option("state", description="On/Off", choices=["on", "off"])
    async def room_auto_name(self, ctx: ApplicationContext, state):
        """Changer automatiquement le nom de la room selon l'activité du leader"""
        
        if not ctx.author.voice:
            await ctx.respond("Vous devez être dans une room et en être le leader pour pouvoir en changer le nom !", ephemeral=True)
            return
        channel = ctx.author.voice.channel
        if not channel.id in rooms:
            await ctx.respond("Vous devez être dans une room et en être le leader pour pouvoir en changer le nom !", ephemeral=True)
            return
        if ctx.author.id != rooms[channel.id]["leader"]:
            await ctx.respond("Vous devez être le leader de la room pour pouvoir changer le nom !", ephemeral=True)
            return

        if state == "on":
            rooms[channel.id]["auto_name"] = True
            log(ctx.author, f'has turned auto-name on in the room "{channel.name}"')
            await ctx.respond("Le nom automatique de la room a été activé.")
        else:
            rooms[channel.id]["auto_name"] = False
            log(ctx.author, f'has turned auto-name off in the room "{channel.name}"')
            await ctx.respond("Le nom automatique de la room a été désactivé.")


    @room_commands.command(name="lock")
    async def lock_room(self, ctx: ApplicationContext):
        """Verrouiller la room pour que seul les membres présents y aient accès"""
        
        if not ctx.author.voice:
            await ctx.respond("Vous devez être dans une room et en être le leader pour pouvoir la verrouiller !", ephemeral=True)
            return
        channel = ctx.author.voice.channel
        if not channel.id in rooms:
            await ctx.respond("Vous devez être dans une room et en être le leader pour pouvoir la verrouiller !", ephemeral=True)
            return
        if ctx.author.id != rooms[channel.id]["leader"]:
            await ctx.respond("Vous devez être le leader de la room pour pouvoir la verrouiller !", ephemeral=True)
            return
        
        for member in channel.members:
            await channel.set_permissions(member, connect=True)
        await channel.set_permissions(ctx.guild.default_role, connect=False)
        
        rooms[channel.id]["locked"] = True
        
        log(ctx.author, f'has locked the room "{channel.name}"')
        await ctx.respond("La room a été verrouillée.")


    @room_commands.command(name="unlock")
    async def unlock_room(self, ctx: ApplicationContext):
        """Déverrouiller la room pour que tout le monde puisse y entrer"""
        
        if not ctx.author.voice:
            await ctx.respond("Vous devez être dans une room et en être le leader pour pouvoir la déverrouiller !", ephemeral=True)
            return
        channel = ctx.author.voice.channel
        if not channel.id in rooms:
            await ctx.respond("Vous devez être dans une room et en être le leader pour pouvoir la déverrouiller !", ephemeral=True)
            return
        if ctx.author.id != rooms[channel.id]["leader"]:
            await ctx.respond("Vous devez être le leader de la room pour pouvoir la verrouiller !", ephemeral=True)
            return
        
        for item in channel.overwrites:
            if type(item) is Member:
                await channel.set_permissions(item, overwrite=None, reason=f"La room a été verrouillée par {ctx.author}")
        await channel.set_permissions(ctx.guild.default_role, overwrite=None, reason=f"La room a été verrouillée par {ctx.author}")
        
        rooms[channel.id]["locked"] = False
        
        log(ctx.author, f'has unlocked the room "{channel.name}"')
        await ctx.respond("La room a été déverrouillée.")



    @room_commands.command(name="blacklist")
    @option("member", description="Le membre à bannir de la room")
    async def blacklist_from_room(self, ctx: ApplicationContext, member: Member):
        """Empêche à un membre de rejoindre la room"""
        
        if not ctx.author.voice:
            await ctx.respond("Vous devez être dans une room et en être le leader pour pouvoir en bannir quelqu'un !", ephemeral=True)
            return
        channel = ctx.author.voice.channel
        if not channel.id in rooms:
            await ctx.respond("Vous devez être dans une room et en être le leader pour pouvoir en bannir quelqu'un !", ephemeral=True)
            return
        if ctx.author.id != rooms[channel.id]["leader"]:
            await ctx.respond("Vous devez être le leader de la room pour pouvoir en bannir quelqu'un !", ephemeral=True)
        
        await channel.set_permissions(member, connect=False, reason="A été banni d'une room")
        
        if member.voice:
            if member.voice.channel.id == channel.id:
                await member.move_to(None)
        
        log(ctx.author, "has blacklisted", member, f'from the room "{channel.name}"')
        await ctx.respond(f"{member.mention} a été banni de la room.")


    @room_commands.command(name="whitelist")
    @option("member", description="Le membre à autoriser dans la room")
    async def whitelist_from_room(self, ctx: ApplicationContext, member: Member):
        """Autoriser un membre à rejoindre la room"""
        
        if not ctx.author.voice:
            await ctx.respond("Vous devez être dans une room et en être le leader pour pouvoir y autoriser quelqu'un !", ephemeral=True)
            return
        channel = ctx.author.voice.channel
        if not channel.id in rooms:
            await ctx.respond("Vous devez être dans une room et en être le leader pour pouvoir y autoriser quelqu'un !", ephemeral=True)
            return
        if ctx.author.id != rooms[channel.id]["leader"]:
            await ctx.respond("Vous devez être le leader de la room pour pouvoir y autoriser quelqu'un !", ephemeral=True)
        
        await channel.set_permissions(member, connect=True, reason="A été autorisé dans une room")

        log(ctx.author, "has whitelisted", member, f'from the room "{channel.name}"')
        await ctx.respond(f"{member.mention} a été autorisé dans la room.")


    @room_commands.command(name="leader")
    @option("member", description="Le membre à définir comme leader")
    async def set_room_leader(self, ctx: ApplicationContext, member: Member):
        """Passer le lead de la room à un membre"""
        
        if not ctx.author.voice:
            await ctx.respond("Vous devez être dans une room et en être le leader pour pouvoir en passer le lead !", ephemeral=True)
            return
        channel = ctx.author.voice.channel
        if not channel.id in rooms:
            await ctx.respond("Vous devez être dans une room et en être le leader pour pouvoir en passer le lead !", ephemeral=True)
            return
        if ctx.author.id != rooms[channel.id]["leader"]:
            await ctx.respond("Vous devez être le leader de la room pour pouvoir en passer le lead !", ephemeral=True)
        
        if rooms[channel.id]["locked"]:
            await channel.set_permissions(member, PermissionOverwrite(connect=True))
        else:
            await channel.set_permissions(member, None)
        
        log(member, f'is the new leader of the room "{channel.name}"')
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


def setup(bot):
    bot.add_cog(VoiceRoom(bot))
    print(" - VoiceRoom")