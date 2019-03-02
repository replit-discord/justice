from disco.bot import Plugin
from disco.api.http import APIException


class JusticePlugin(Plugin):

    @classmethod
    def get_docs(cls, name: str = None):
        funcs = []
        for attr in cls.__dict__.values():
            if hasattr(attr, 'docs'):
                if name and name == attr.docs[0]:
                    return name.docs
                if not name:
                    funcs.append(name.docs)
        return funcs

    def handle_exception(self, greenlet, event):
        if isinstance(greenlet.exception, APIException):
            if greenlet.exception.code == 403:  # Insufficient permissions
                event.msg.reply("Sorry, but I cannot do that. Fix my permissions and try again.")
            elif greenlet.exception.code >= 500:   # Server error
                event.msg.reply("Discord is having issues right now, try again later.")
            elif greenlet.exception.code >= 400:  # We did something bad
                event.msg.reply("Appologies, we messed up, this will be recorded and fixed in the future.")
                greenlet.get()

    @classmethod
    def add_meta_deco(cls, meta):
        def deco(f):
            docs = f.__doc__
            if docs:
                title, desc = docs.split("\n")[0], '\n'.join(docs.split('\n')[1:])
                desc = desc.strip()
                f.docs = meta['args'][0], title, desc

            if not hasattr(f, 'meta'):
                f.meta = []

            f.meta.append(meta)

            return f

        return deco
