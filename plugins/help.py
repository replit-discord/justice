from utils.safe import JusticePlugin

from disco.types.message import MessageEmbed


class HelpPlug(JusticePlugin):
    """Help | Display command details"""

    __name__ = "HelpPlug"

    @JusticePlugin.command("help", "[name:str]")
    def show_help(self, event, name: str = None):
        """Explain commands or list them

        The help commands provides an easy way for you to learn about a certain command, or list available ones.

        If you want to access a specific command, type `]help <name>`, For example, `]help ban`.

        If you want to display a list all command categories, simply type `]help` with nothing else.

        If you want to list all commands in a category, simply type `]help <Name>`, For example, `]help Mod`

        Tip: commands will always be all lower case, command categories are Titled.
        """

        if not name:
            embed = MessageEmbed()
            embed.color = 0x00FFFF
            embed.title = "List Command Categories"
            embed.description = "If you want to see how to use the help command, type `]help help`, otherwise, " \
                                "below are the available command categories."
            for plugin in self.bot.plugins.values():
                name, desc = plugin.__doc__.split(' | ')
                embed.add_field(name=name, value=desc, inline=False)
            event.msg.reply(embed=embed)
        elif name.title() == name:
            for plugin in self.bot.plugins.values():
                if name in plugin.__doc__.lower():
                    break
            else:
                return event.msg.reply("Sorry, but I could not find the category '{0}'".format(name))

            embed = MessageEmbed()
            embed.color = 0x00FFFF
            embed.title = plugin.__doc__

            for func in plugin.meta_funcs:
                if hasattr(func, 'docs'):
                    embed.add_field(name=func.docs[0], value=func.docs[1], inline=False)

            event.msg.reply(embed=embed)
        else:
            for plugin in self.bot.plugins.values():
                for func in plugin.meta_funcs:
                    if hasattr(func, 'docs') and func.docs[0] == name:
                        embed = MessageEmbed()
                        embed.title = func.docs[1]
                        embed.color = 0x00FFFF
                        embed.description = func.docs[2]
                        return event.msg.reply(embed=embed)
            event.msg.reply("Sorry, but I could not find the command '{0}'".format(name))


del JusticePlugin  # We don't want disco to load this plugin
