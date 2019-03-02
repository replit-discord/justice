import utils.config as config
from utils.deco import parse_member, require
from utils.safe import JusticePlugin

from disco.bot.command import CommandEvent
from disco.types.channel import ChannelType
from disco.types.message import Message, MessageEmbed, MessageEmbedThumbnail
from disco.types.permissions import Permissions
from disco.types.guild import GuildMember
from disco.types.user import User


class WatchPlug(JusticePlugin):
    """Watch | Observe others"""

    def load(self, ctx):
        self.msg_cache = {}

    @staticmethod
    def create_embed(event_name: str,
                     event_link: str,
                     user: User,
                     *args, **kwargs):

        embed = MessageEmbed()
        embed.title = event_name
        embed.url = event_link
        embed.thumbnail = MessageEmbedThumbnail(url=user.avatar_url)
        args_desc = "\n\n".join(args)
        kwargs_desc = "\n\n".join("**{0}:\n{1}**".format(name, value) for name, value in kwargs.items())
        embed.description = "\n\n".join((args_desc, kwargs_desc))
        embed.color = 0x00FFFF
        return embed

    @require(Permissions.ADMINISTRATOR)
    @parse_member
    @JusticePlugin.command("watch", "<member:str>")
    def observe_member(self, event: CommandEvent, member: GuildMember):
        """Observe another user

        This command will create a private channel, where actions such as sending a message, editing, deleting, adding
        reactions and removing reactions are recorded. Staff members can delete the channels when done, or do ]close
        """
        watching_data = self.bot.storage["WATCHING"].data
        if member.id in watching_data:
            return event.msg.reply("Sorry, but I'm watching that user in <#{0}>".format(watching_data[member.id]))

        new_channel = self.client.api.guilds_channels_create(
            config.GUILD_ID,
            ChannelType.GUILD_TEXT,
            member.user.username,
            parent_id=config.WATCH_CATEGORY)

        watching_data[str(member.id)] = new_channel.id  # Gah, JSON, accept int keys!
        event.msg.add_reaction("👍")
        new_channel.send_message("Watching {0} | Requested by {1}".format(member.mention, event.author.mention))

    def unwatch(self, select_channel_id: int, delete: bool=True):
        watching_data = self.bot.storage["WATCHING"].data
        for user_id, channel_id in watching_data.items():
            if channel_id == select_channel_id:
                del watching_data[user_id]
                marked = []
                for msg_id, data in self.msg_cache.items():
                    if data['user'] == int(user_id):
                        marked.append(msg_id)
                for m_id in marked:
                    del self.msg_cache[m_id]
                if delete:
                    self.client.api.channels_delete(channel_id, reason="Watcher removed")
                return True
        else:
            return False

    @require(Permissions.ADMINISTRATOR)
    @JusticePlugin.command("close")
    def close_watcher(self, event: CommandEvent):
        """Remove watcher from user

        You must use this command in a channel that's being used to watch someone. It will clear the cache and stop
        looking for their messages. It will also then delete that channel.
        """
        if not self.unwatch(event.msg.channel_id):
            event.msg.reply("Sorry, not this channel is nt being used to watch someone")

    @JusticePlugin.listen("ChannelDelete")
    def on_channel_del(self, channel):
        self.unwatch(channel.id, delete=False)

    @JusticePlugin.listen("MessageCreate")
    @JusticePlugin.listen("MessageUpdate")
    def on_message(self, msg: Message):
        watching_data = self.bot.storage["WATCHING"].data
        if str(msg.author.id) in watching_data:
            self.msg_cache[msg.id] = {"content": msg.content, "user": msg.author.id}
            link = "https://discordapp.com/channels/{0}/{1}/{2}".format(msg.channel.guild_id, msg.channel_id, msg.id)
            new_msg_embed = self.create_embed("Edited Message" if msg.edited_timestamp else "New Message",
                                              link, msg.author, msg.content)
            self.client.api.channels_messages_create(watching_data[str(msg.author.id)], embed=new_msg_embed)

    @JusticePlugin.listen("MessageDelete")
    def on_message_edit(self, msg_data):
        watching_data = self.bot.storage["WATCHING"].data
        if msg_data.id in self.msg_cache:
            link = "https://discordapp.com/channels/{0}/{1}/{2}".format(
                msg_data.guild.id, msg_data.channel_id, msg_data.id)
            member = self.client.api.guilds_members_get(config.GUILD_ID, self.msg_cache[msg_data.id]["user"])
            del_msg_embed = self.create_embed("Deleted Message", link,
                                              member.user, self.msg_cache[msg_data.id]["content"])
            self.client.api.channels_messages_create(watching_data[str(self.msg_cache[msg_data.id]["user"])],
                                                     embed=del_msg_embed)
