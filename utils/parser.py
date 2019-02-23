class ParseError(Exception):
    pass


multiplier = {
    "s": 1,
    "m": 60,
    "h": 60 * 60,
    "d": 60 * 60 * 24
}


def time_parse(content: str):
    total = 0
    parts = content.split(' ')
    for part in parts:
        mult = multiplier.get(part[-1])
        if mult is None or not part[:-1].isnumeric():
            raise ParseError
        total += multiplier[part[-1]] * int(part[:-1])
    return total
