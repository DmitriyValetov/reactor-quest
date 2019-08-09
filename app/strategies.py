import random
from datetime import datetime

from app.events import factory, terrors_factory, staff_factory, govs_factory


def staff_1(reactor, source):
    events = []
    timestamp = datetime.utcnow().isoformat()
    if reactor.rate > 5:
        events.append({'name': 'rod_down', 'work': 1, 'source': source,
                       'timestamp': timestamp})
    if reactor.rate > 8:
        events.append({'name': 'boron', 'work': 1, 'source': source,
                       'timestamp': timestamp})
    if reactor.state > 90 and reactor.rate > 1:
        events.append({'name': 'rod_down', 'work': 1, 'source': source,
                       'timestamp': timestamp})
    if reactor.state == 100 and reactor.rate > 0:
        events.append({'name': 'scram', 'work': 1, 'source': source,
                       'timestamp': timestamp})
    if reactor.state > 100:
        events.append({'name': 'scram', 'work': 1, 'source': source,
                       'timestamp': timestamp})
    if reactor.state < 50 and reactor.rate <= 0:
        events.append({'name': 'rod_up', 'work': 1, 'source': source,
                       'timestamp': timestamp})
    return events


def govs_1(reactor, source):
    events = []
    timestamp = datetime.utcnow().isoformat()
    if reactor.state < 50 and reactor.rate <= 0:
        name = random.choice(list(govs_factory))
        events.append({'name': name, 'work': 1, 'source': source,
                       'timestamp': timestamp})
    return events


def reactor_1(reactor, source):
    events = []
    timestamp = datetime.utcnow().isoformat()
    if 0 < reactor.state < 50:
        events.append({'name': 'iodine', 'work': 1, 'source': source,
                       'timestamp': timestamp})
    if random.uniform(0, 1) < reactor.chance:
        events.append({'name': 'boom', 'work': 1, 'source': source,
                       'timestamp': timestamp})
    return events


def terrors_1(reactor, source):
    events = []
    timestamp = datetime.utcnow().isoformat()
    name = random.choice(list(terrors_factory))
    events.append({'name': name, 'work': 1, 'source': source,
                   'timestamp': timestamp})
    return events


strategy_factory = {
    'staff_1': staff_1,
    'terrors_1': terrors_1,
    'govs_1': govs_1,
    'reactor_1': reactor_1
}
