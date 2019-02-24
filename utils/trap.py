from datetime import datetime
import weakref

from disco.bot import Plugin


def creation_date(snowflake: int) -> datetime:
    return datetime.fromtimestamp((snowflake >> 22) + 1420070400000)


class RaidSession:

    def __init__(self):
        self.active_raid = False
        self._severity = {}
        self.raiders = weakref.WeakValueDictionary()

    @property
    def severity(self):
        return sum(self._severity.values())

    def change_severity(self, value: int, pool: str):
        self._severity[pool] = value

    def attach(self, rid: int, func, *args, **kwargs):  # I want to use weakref, so this is a work around.
        r = self.raiders.get(rid)
        if r is None:
            r = Raider(rid)
            self.raiders[rid] = r
        func(r, *args, **kwargs)


class Pool:

    def __init__(self, session: RaidSession, plugin: Plugin, interval: int):
        self.session = session
        self.plugin = plugin
        self.interval = interval
        self.pool = []
        self.past_severity = 0
        self.plugin.register_schedule(self.drain, interval)

    def change_severity(self, value: int):
        self.session.change_severity(value, self.__class__.__name__)

    def drain(self):
        if self.pool and not self.session.active_raid:
            self.pool.pop(0)

    def check_contents(self):
        raise NotImplementedError

    def fill(self, obj):
        self.pool.append(obj)
        self.check_contents()


class MemberPool(Pool):

    def __init__(self, session: RaidSession, plugin: Plugin, inveral: int = 10, max_members: int = 3):
        self.max_members = max_members
        super().__init__(session, plugin, inveral)

    def fill(self, member):
        self.session.attach(member.id, Raider.set_join_raid, member)
        super().fill(member)

    def check_contents(self):
        severity = len(self.pool) // self.max_members
        if all(member.user.avatar is None for member in self.pool):
            severity += 2
        if len(self.pool) > self.max_members:
            init_creation = creation_date(self.pool[0].id)
            for member in self.pool[1:]:
                member_creation = creation_date(member.id)
                works = False
                for time_type in ('year', 'month', 'day'):
                    if getattr(init_creation, time_type) != getattr(member_creation, time_type):
                        break
                else:
                    works = True
                if not works:
                    break
            else:
                severity += 4
            init_name = self.pool[0].user.username
            if all(member.user.username == init_name for member in self.pool):
                severity += 6
        if severity != self.past_severity:
            self.past_severity = severity
            self.change_severity(severity)


class MessagePool(Pool):

    def __init__(self, session: RaidSession, plugin: Plugin, inveral: int = 2, max_messages: int = 6):
        self.max_messages = max_messages
        super().__init__(session, plugin, inveral)

    def fill(self, msg):
        self.session.attach(msg.author.id, Raider.add_msg, msg)
        super().fill(msg)

    def check_contents(self):
        severity = len(self.pool) // self.max_messages
        init_message = self.pool[0].content
        if all(m.content == init_message for m in self.pool):
            severity += 3
        init_author = self.pool[0].author.id
        if all(m.author.id == init_author for m in self.pool):
            severity += 1
        if severity > self.past_severity:
            self.past_severity = severity
            self.change_severity(severity)


class Raider:

    def __init__(self, id: int):
        self.id = id
        self._join_raid = lambda: None
        self.msg_raid = weakref.WeakSet()

    @property
    def mention(self):
        return "<@{0}>".format(self.id)

    @property
    def join_raid(self):
        return self._join_raid()

    def set_join_raid(self, value):
        value._link = self
        self._join_raid = weakref.ref(value)

    def msg_count(self):
        return len(self.msg_raid)

    def add_msg(self, message):
        message._link = self
        self.msg_raid.add(message)
