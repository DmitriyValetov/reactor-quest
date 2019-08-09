def test(reactor):
    pass


def tip(reactor):
    reactor.acc += 1


def iodine(reactor):
    reactor.acc -= 1


def boron(reactor):
    reactor.acc -= 1


def pump_down(reactor):
    reactor.queue.append({'name': 'steam', 'work': 1, 'source': 'reactor'})


def pump_up(reactor):
    reactor.queue.append({'name': 'water', 'work': 1, 'source': 'reactor'})


def pump_break(reactor):
    reactor.queue.append({'name': 'steam', 'work': 1, 'source': 'reactor'})


def pump_blow_up(reactor):
    reactor.queue.append({'name': 'steam', 'work': 1, 'source': 'reactor'})


def bribe_chief_engineer(reactor):
    reactor.queue.append({'name': 'rod_up', 'work': 1, 'source': 'reactor'})


def press_operators(reactor):
    reactor.queue.append({'name': 'rod_up', 'work': 1, 'source': 'reactor'})


def fire(reactor):
    reactor.queue.append({'name': 'pump_down', 'work': 1, 'source': 'reactor'})


def rod_down(reactor):
    reactor.acc -= 1


def rod_up(reactor):
    reactor.acc += 1


def water(reactor):
    reactor.acc -= 1


def steam(reactor):
    reactor.acc += 1


def scram(reactor):
    reactor.state = 0
    reactor.rate = 0
    reactor.acc = 0
    reactor.scram_cnt += 1
    reactor.safe_cnt = 0
    reactor.zero_cnt += 1


def boom(reactor):
    reactor.state = 0
    reactor.rate = 0
    # reactor.acc = 0
    reactor.boom_cnt += 1
    reactor.safe_cnt = 0
    reactor.zero_cnt += 1


def deenergize(reactor):
    reactor.queue.append({'name': 'pump_down', 'work': 1, 'source': 'reactor'})


def replace_boron(reactor):
    reactor.acc += 1


def anti_terrorist_operation(reactor):
    reactor.ato_cnt += 1


factory = {
    'rod_up': rod_up,
    'rod_down': rod_down,
    'pump_up': pump_up,
    'pump_down': pump_down,
    'pump_break': pump_break,
    'pump_blow_up': pump_blow_up,
    'steam': steam,
    'water': water,
    'iodine': iodine,
    'deenergize': deenergize,
    'replace_boron': replace_boron,
    'boron': boron,
    'boom': boom,
    'tip': tip,
    'scram': scram,
    'bribe_chief_engineer': bribe_chief_engineer,
    'press_operators': press_operators,
    'anti_terrorist_operation': anti_terrorist_operation,
    'fire': fire,
    'test': test
}

staff_factory = {
    'scram': scram,
    'rod_up': rod_up,
    'rod_down': rod_down,
    'pump_up': pump_up,
    'pump_down': pump_down,
    'boron': boron
}

terrors_factory = {
    'pump_break': pump_break,
    'pump_blow_up': pump_blow_up,
    'replace_boron': replace_boron,
    'deenergize': deenergize,
    'fire': fire
}

govs_factory = {
    # 'anti_terrorist_operation': anti_terrorist_operation,
    'bribe_chief_engineer': bribe_chief_engineer,
    'press_operators': press_operators,
    'tip': tip
}
