import time as t

import utils.config as config
from utils.deco import require, parse_member
from utils.parser import time_parse, ParseError
from utils.safe import JusticePlugin

from disco.bot.command import CommandEvent
from disco.types.guild import GuildMember
from disco.types.permissions import Permissions
from gevent import sleep, spawn


class ModPlug(JusticePlugin):
    """Mod | Moderation actions"""

    @JusticePlugin.listen("Ready")
    def on_ready(self, event):
        mute_records = self.bot.storage["MUTES"].data
        for member_id, details in mute_records.items():
            to_finish = (details["start"] + details["length"]) - int(t.time())
            print("Umute", member_id, to_finish)
            spawn(self.unmute, member_id, to_finish)

    @require(Permissions.KICK_MEMBERS)
    @parse_member
    @JusticePlugin.command("kick", "<member:str> [reason:str...]")
    def kick_user(self, event: CommandEvent, member: GuildMember, reason: str = None):
        """Kick a member

        A simple way to remove someone from the guild, without getting you hands dirty.

        This bot supports a variety of ways to provider users, so for example you can do:
        `]kick 09832098349` (Ban user from their ID)
        `]kick @BadUser5456` (Ban user from mention)
        `]kick BadUser5456#0001` (Ban user from name + discriminator)

        You can also specify the reason for the ban:
        `]kick @BadUser5456 Provoking other members of the guild`
        """
        member.kick(reason=reason)
        event.msg.add_reaction("👍")

    @require(Permissions.BAN_MEMBERS)
    @parse_member
    @JusticePlugin.command("ban", "<member:str> <days:int> [reason:str...]")
    def ban_user(self, event: CommandEvent, member: GuildMember, days: int, reason: str = None):
        """Ban a member

        Easily and permanently ban a user from the guild

        You must provide the user, and the amount of messages to delete from the past X days.

        This bot supports a variety of ways to provider users, so for example you can do:
        `]ban 09832098349 0` (Ban user from their ID, don't remove any messages)
        `]ban @BadUser5456 1` (Ban user from mention, remove messages from the past day)
        `]ban BadUser5456#0001 14` (Ban user from name + discriminator, remove messages from past 2 weeks)

        You can also specify the reason for the ban:
        `]ban @BadUser5456 7 Spamming invite links in chat`
        """
        member.ban(delete_message_days=days, reason=reason)
        event.msg.add_reaction("👍")

    def unmute(self, member_id: int, sleep_delay: int):
        sleep(sleep_delay)
        channels = self.client.api.guilds_channels_list(config.GUILD_ID)
        for channel in channels.values():
            overwrite = channel.overwrites.get(int(member_id))
            if overwrite:
                overwrite.deny.value &= ~Permissions.SEND_MESSAGES.value
                overwrite.deny.value &= ~0x00000040
                if overwrite.allow.value == 0 and overwrite.deny.value == 0:
                    overwrite.delete()
                else:
                    overwrite.save()
        del self.bot.storage["MUTES"].data[member_id]

    @require(Permissions.MANAGE_CHANNELS)
    @parse_member
    @JusticePlugin.command("silence", "<member:str> [time:str...]")
    def mute_user(self, event: CommandEvent, member: GuildMember, time: str = None):
        """Silence a member

        Create overwrites on all necessary channels, and prevent the user from typing there.
        You can also add a time limit, where after the time is over, it will unsilence them.

        This bot supports a variety of ways to provider users, so for example you can do:
        `]silence 09832098349` (Ban user from their ID, won't unslience after some time)
        `]silence @BadUser5456 1m 30s` (Ban user from mention, unsilence after 1 min and 30 seconds)
        `]silence BadUser5456#0001 10d 2h` (Ban user from name + discriminator, unsilence after 10 days and 2 hours)
        """
        if time:
            try:
                total_time = time_parse(time)
            except ParseError:
                return event.msg.reply("Sorry, I don't recognize '{0}' as a valid time.".format(time))
            else:
                if total_time < 30 or total_time > 31 * 24 * 60 * 60:
                    return event.msg.reply("Sorry, the time must be >30sec and <1 month.")

                mute_record = self.bot.storage["MUTES"].data
                mute_record[member.id] = {
                    "start": int(t.time()),
                    "length": total_time
                }
                spawn(self.unmute, member.id, total_time)

        for channel in event.guild.channels.values():
            everyone_ow = channel.overwrites.get(channel.guild_id)
            if everyone_ow and not everyone_ow.deny.value & Permissions.SEND_MESSAGES.value:
                channel.create_overwrite(member, deny=0x00000840)
        event.msg.add_reaction("👍")

    @require(Permissions.MANAGE_CHANNELS)
    @parse_member
    @JusticePlugin.command("unmute", "<member:str>")
    def unmute_user(self, event: CommandEvent, member: GuildMember):
        """Unslience a member

        Remove overwrites on channels that have been blocked by the silence, not needed if you specied a time for
        the silence command.

        This bot supports a variety of ways to provider users, so for example you can do:
        `]unmute 09832098349` (Mute user from their ID)
        `]unmute @BadUser5456` (Mute user from mention)
        `]unmute BadUser5456#0001` (Mute user from name + discriminator)
        """
        self.unmute(member.id, 0)
        event.msg.reply("👍")


del JusticePlugin  # We don't want disco to load this plugin
