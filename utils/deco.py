from functools import wraps

from disco.bot.command import CommandEvent


def require(*perms):
    def func_wrap(func):
        @wraps(func)
        def wrapper(self, event: CommandEvent, *args, **kwargs):
            perm_code = event.channel.get_permissions(event.author.id)
            if perm_code.can(*perms):
                func(self, event, *args, **kwargs)
            else:
                event.msg.reply("Sorry, but you do not have sufficient privileges to do this.")
        return wrapper
    return func_wrap


def parse_member(func):
    @wraps(func)
    def wrapper(self, event: CommandEvent, member: str, *args, **kwargs):
        if member.isnumeric():
            real_member = event.guild.members.get(int(member))
        elif len(event.msg.mentions) == 1:
            real_member = event.guild.members.get(next(iter(event.msg.mentions)))  # Epic Hacks lmao
        else:
            for guild_member in event.guild.members.values():

                if "#".join([guild_member.user.username, guild_member.user.discriminator]) == member:
                    real_member = guild_member
                    break
                else:
                    real_member = None

        if real_member is None:
            event.msg.reply("Sorry, but we could not find the user ({user})".format(user=member))
        else:
            func(self, event, real_member, *args, **kwargs)
    return wrapper
