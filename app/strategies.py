import random

from app.events import factory, terrors_factory, staff_factory, govs_factory


def staff_1(reactor, source):
    events = []
    if reactor.state < 25 and reactor.rate <= 0:
        events.append({'name': 'rod_up', 'source': source})
    if reactor.state > 75 and reactor.rate >= 0:
        events.append({'name': 'rod_down', 'source': source})
    return events


def govs_1(reactor, source):
    events = []
    if reactor.state < 90 and reactor.rate < 0:
        if random.random() < 0.1:
            events.append({'name': 'press_operators', 'source': source})
    return events


def reactor_1(reactor, source):
    events = []
    if 0 < reactor.state < 50:
        events.append({'name': 'iodine', 'source': source})
    if random.uniform(0, 1) < reactor.chance:
        events.append({'name': 'boom', 'source': source})
    return events


def terrors_1(reactor, source):
    events = []
    if reactor.state > 50:
        if random.random() < 0.1:
            events.append({'name': 'pump_break', 'source': source})
    return events


def staff_rand(reactor, source):
    events = []
    if random.random() < 0.05:
        name = random.choice(list(staff_factory))
        events.append({'name': name, 'source': source})
    return events


def terrors_rand(reactor, source):
    events = []
    if random.random() < 0.05:
        name = random.choice(list(terrors_factory))
        events.append({'name': name, 'source': source})
    return events


def govs_rand(reactor, source):
    events = []
    if random.random() < 0.05:
        name = random.choice(list(govs_factory))
        events.append({'name': name, 'source': source})
    return events


def reactor_2(reactor, source):
    events = []
    return events


strategy_factory = {
    'staff_1': staff_1,
    'terrors_1': terrors_1,
    'govs_1': govs_1,
    'reactor_1': reactor_1,
    'staff_rand': staff_rand,
    'terrors_rand': terrors_rand,
    'govs_rand': govs_rand,
    'reactor_2': reactor_2
}
