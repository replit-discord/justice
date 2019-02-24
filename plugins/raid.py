import utils.config as config
from utils.deco import require
from utils.safe import JusticePlugin
from utils.trap import MemberPool, MessagePool, RaidSession

from disco.bot import CommandLevels
from disco.types.message import MessageEmbed
from disco.types.permissions import Permissions


class RaidPlug(JusticePlugin):
    """Raid | Detect raids"""

    def load(self, ctx):
        self.session = RaidSession()
        self.join_pool = MemberPool(self.session, self)
        self.msg_pool = MessagePool(self.session, self)

    def check_severity(self):
        if self.session.severity > config.SEVERITY_TOLERANCE and not self.session.active_raid:
            channel = self.client.api.channels_get(config.WARN_CHANNEL)
            channel.send_message("Attention @everyone, severity level has reached **{1}**\n\nTriggering!".format(
                config.GUILD_ID,
                self.session.severity
            ))
            self.session.active_raid = True

    @JusticePlugin.listen("GuildMemberAdd")
    def on_join(self, member):
        self.join_pool.fill(member)
        self.check_severity()

    @JusticePlugin.listen("MessageCreate")
    def on_message(self, msg):
        if msg.author.bot or msg.member.permissions.can(Permissions.ADMINISTRATOR):
            return
        self.msg_pool.fill(msg)
        self.check_severity()

    @require(Permissions.ADMINISTRATOR)
    @JusticePlugin.command("raiders")
    def show_raiders(self, event: CommandLevels):
        """List raiders

        This all of the raiders that have been caught, so they can be processed. This command requires no arguments,
        but will not work if the server isn't being raided (or we haven't detected a raid yet).
        """
        embed = MessageEmbed()
        embed.title = "Possible Raiders: (Anti-Raid not triggered)" if not self.session.active_raid else "Raiders:"
        embed.color = 0x00FFFF
        embed.description = ""
        for raider in self.session.raiders.values():
            triggered = []
            if raider.join_raid:
                triggered.append("Joined during raid")
            elif raider.msg_raid:
                triggered.append("Sent messages during raid ({0})".format(raider.msg_count()))
            embed.description += "{0} - {1}\n".format(raider.mention, ". ".join(triggered))
        event.msg.reply(embed=embed)


del JusticePlugin
