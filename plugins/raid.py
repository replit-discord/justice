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

        Lists all of the raiders that have been caught, so they can be processed. This command requires no arguments,
        and will alert you if the server isn't actually being raided (so the people listed might not be doing anything
        wrong.
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

    @require(Permissions.ADMINISTRATOR)
    @JusticePlugin.command("reset")
    def reset_pools(self, event):
        """Reset raid trigger

        This command will empty all pools, storing messages and people. In addition to clearing data, it will disable
        the raid alarm, and allow pools to start emptying again.
        """
        self.session.active_raid = False
        self.msg_pool.pool.clear()
        self.join_pool.pool.clear()
        event.msg.add_reaction("👍")

    @require(Permissions.ADMINISTRATOR)
    @JusticePlugin.command("raid")
    def raid_summary(self, event):
        """View raid summary

        This command will allow a moderator to view details about the raid. If there is not a raid it will still provide
        information. Information includes severity, pool sizes, and a sample of content in the pools.
        """
        embed = MessageEmbed()
        embed.color = 0x00FFFF
        embed.title = "Under Raid: " if self.session.active_raid else "Raid Not Triggered"
        if self.session.active_raid and self.session.severity < config.SEVERITY_TOLERANCE * 1.5:
            embed.title += "Small"
        elif self.session.active_raid and self.session.severity < config.SEVERITY_TOLERANCE * 2:
            embed.title += "Medium"
        elif self.session.active_raid:
            embed.title += "Large"

        desc = """
        **Join Pool:** {joins}
        **Message Pool:** {msgs}
        **Severity / Tolerance:** {severity} / {tolerance}
        **Joins Samples:**
        \t{join_samples}
        **Message Samples:**
        \t{msg_samples}
        """.lstrip()

        embed.description = desc.format(
            joins=len(self.join_pool.pool),
            msgs=len(self.msg_pool.pool),
            severity=self.session.severity,
            tolerance=config.SEVERITY_TOLERANCE,
            join_samples="\n\t".join("<@{0}>".format(r.id) for _, r in zip(range(5), self.join_pool.pool)),
            msg_samples="\n\t".join("{0}: {1}".format(m.author.mention, m.content)
                                    for _, m in zip(range(5), self.msg_pool.pool))
        )
        event.msg.reply(embed=embed)


del JusticePlugin
