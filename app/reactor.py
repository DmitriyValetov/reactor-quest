from datetime import datetime
import time
# import matplotlib.pyplot as plt
import sqlite3
import json
import os

from app.events import factory
from app.strategies import strategy_factory
from app.counts import counts_factory


class Reactor:
    def __init__(self, step=1, work=120, chance_rate=0.05,
                 reactor_strategy='reactor_1', counts='state_range'):
        self.step = step  # state update period in seconds
        self.cur_step = 0  # current step
        self.cur_timestamp = None
        self.work = work  # working time in steps
        self.state = 0  # state
        self.rate = 0  # state rate per step
        self.events = {}  # current step events
        self.events_start = {}  # events start time step
        self.events_end = {}  # events end time step
        self.events_to_stop = {}  # events to stop (set 0 status at db)
        self.events_to_init = {}  # events to init (set start, end at db)
        self.chance = 0  # boom chance for states > 100 (checked every step)
        self.chance_rate = chance_rate  # chance rate per step for states > 100
        # self.times = []  # times history by steps
        # self.states = []  # states history
        # self.rates = []  # rates history
        # self.chances = []  # disaster chances history
        self.dump_path = 'reactor.json'  # file or db path
        self.db = False  # dump to db?
        self.reactor_strategy = reactor_strategy
        self.counts = counts
        self.staff_cnt = 0
        self.govs_cnt = 0
        self.terrors_cnt = 0
        self.no_one_cnt = 0
        self.booms_cnt = 0

    def run(self, plot=True,
            dump_path='reactor.json', reset=True, last_dump=False,
            simulate=False, simulate_teams=None, simulate_strats=None):
        self.dump_path = dump_path
        if os.path.splitext(dump_path)[1] == '.db':
            self.db = True
            if reset:
                self.reset_db()
            else:  # load last state
                self.load_db()
        if plot:
            self.create_plot()
        while self.cur_step < self.work:
            self.cur_timestamp = datetime.utcnow()
            if simulate:
                self.simulate(simulate_teams, simulate_strats)
            time.sleep(self.step)  # wait for the next step
            self.update()
            if last_dump:
                if self.cur_step == self.work:
                    self.dump()
            else:
                self.dump()
            if plot:
                self.plot()
            self.cur_step += 1

    def update(self):
        prev_state = self.state
        # update events
        self.events = {}
        if self.db:
            self.update_events_db()
        else:
            self.update_events_local()
        # run events
        self.events_to_init = {}
        self.events_to_stop = {}
        for i, (k, v) in enumerate(self.events.items()):
            factory[v['name']](k, self)
        # update chance and fix state
        if 0 <= self.state <= 100:
            self.chance -= self.chance_rate
        else:  # self.state > 100
            k = self.state / 100
            self.chance += k * self.chance_rate
        if self.chance < 0:
            self.chance = 0
        if self.state < 0:
            self.state = 0
        # update rate
        self.rate = self.state - prev_state
        # update teams scores
        counts_factory[self.counts](self)
        # update history
        # self.times.append(self.cur_timestamp)
        # self.states.append(self.state)
        # self.rates.append(self.rate)
        # self.chances.append(self.chance)

    def dump(self):
        if self.db:
            self.dump_db()
        else:
            if os.path.splitext(self.dump_path)[1] == '.json':
                self.dump_json()

    def simulate(self, simulate_teams=None, simulate_strats=None):
        if simulate_strats is None:
            simulate_strats = ['staff_1', 'terrors_1', 'govs_1']
        if simulate_teams is None:
            simulate_teams = ['staff', 'terrors', 'govs']
        staff_events = strategy_factory[simulate_strats[0]](self, 'staff')
        terrors_events = strategy_factory[simulate_strats[1]](self, 'terrors')
        govs_events = strategy_factory[simulate_strats[2]](self, 'govs')
        events = list()
        if 'staff' in simulate_teams:
            events.extend(staff_events)
        if 'terrors' in simulate_teams:
            events.extend(terrors_events)
        if 'govs' in simulate_teams:
            events.extend(govs_events)
        if self.db:
            con = sqlite3.connect(self.dump_path)
            try:
                cur = con.cursor()
                cur.executemany('INSERT INTO events VALUES (?, ?, ?, ?, ?)',
                                [(None, json.dumps(x), 1, None, None)
                                 for x in events])
                con.commit()
            except Exception as e:
                print(e)
            finally:
                con.close()
        else:
            self.events.update(events)

    def update_events_local(self):
        events = strategy_factory[self.reactor_strategy](self, 'reactor')
        self.events.update(events)

    def update_events_db(self):
        events = strategy_factory[self.reactor_strategy](self, 'reactor')
        con = sqlite3.connect(self.dump_path)
        try:
            cur = con.cursor()
            cur.executemany('INSERT INTO events VALUES (?, ?, ?, ?, ?)',
                            [(None, json.dumps(x), 1, None, None)
                             for x in events])
            con.commit()
            events_json = cur.execute(
                '''SELECT * FROM events WHERE status > 0''').fetchall()
        except Exception as e:
            print(e)
        else:
            for e in events_json:
                rowid, event_json, status, start, end = e
                event = json.loads(event_json)
                if start is not None:
                    self.events_start[int(rowid)] = start
                if end is not None:
                    self.events_end[int(rowid)] = end
                self.events[int(rowid)] = event
        finally:
            con.close()

    def dump_db(self):
        state = self.__dict__.copy()
        state.pop('grid', None)  # from colab plot
        state.pop('events', None)
        state.pop('events_start', None)
        state.pop('events_to_stop', None)
        state.pop('times', None)
        state.pop('rates', None)
        state.pop('states', None)
        state.pop('chances', None)
        state_json = json.dumps(
            state,
            default=lambda x: x.isoformat() if isinstance(x, datetime) else x)
        con = sqlite3.connect(self.dump_path)
        try:
            cur = con.cursor()
            cur.execute('INSERT INTO states VALUES (?, ?)', [None, state_json])
            cur.executemany('UPDATE events SET status = ? WHERE id = ?',
                            [(0, k) for k in self.events_to_stop])
            cur.executemany('UPDATE events SET start = ?, end = ? WHERE id = ?',
                            [(self.events_start[k], self.events_end[k], k)
                             for k in self.events_to_init])
            con.commit()
        except Exception as e:
            print(e)
        finally:
            con.close()

    def dump_json(self):
        state = self.__dict__.copy()
        state.pop('grid', None)  # from colab plot
        state.pop('events', None)
        state.pop('events_start', None)
        state.pop('events_to_stop', None)
        state.pop('times', None)
        state.pop('rates', None)
        state.pop('states', None)
        state.pop('chances', None)
        with open(self.dump_path, 'w') as f:
            json.dump(state, f, default=lambda x: x.isoformat() if isinstance(
                x, datetime) else x)

    def load_db(self):
        con = sqlite3.connect(self.dump_path)
        try:
            cur = con.cursor()
            cur.execute("SELECT * FROM states ORDER BY id DESC LIMIT 1")
            rowid, last_state_json = cur.fetchone()
        except Exception as e:
            print(e)
        else:
            last_state = json.loads(last_state_json)
            cur_timestamp_str = last_state['cur_timestamp']
            last_state['cur_timestamp'] = datetime.strptime(
                cur_timestamp_str, "%Y-%m-%dT%H:%M:%S.%f")
            for k in last_state:
                self.__dict__[k] = last_state[k]
        finally:
            con.close()

    def reset_db(self):
        con = sqlite3.connect(self.dump_path)
        try:
            cur = con.cursor()
            cur.execute('''DROP TABLE IF EXISTS states''')
            cur.execute('''CREATE TABLE IF NOT EXISTS states 
            (id INTEGER PRIMARY KEY, data TEXT)''')
            cur.execute('''DROP TABLE IF EXISTS events''')
            cur.execute('''CREATE TABLE IF NOT EXISTS events
            (id INTEGER PRIMARY KEY, data TEXT, status INT, 
            start INT, end INT)''')
        except Exception as e:
            print(e)
        finally:
            con.close()

    def create_plot(self):
        # self.grid = widgets.Grid(3, 2, header_row=True, header_column=True)
        pass

    def plot(self):
        print('\ncur step: {}'.format(self.cur_step))
        print('{:^4}|{:^4}|{:^7}|{:^5}|{:^10}|{:^20}|'.format(
            'n', 'id', 'start', 'end', 'source', 'event'))
        print('-'.join(['' for _ in range(57)]))
        print('\n'.join(
            ['{:^4}|{:^4}|{:^7}|{:^5}|{:^10}|{:^20}|'.format(
                i + 1, k, self.events_start[k], self.events_end[k],
                v['source'], v['name'])
                for i, (k, v) in enumerate(self.events.items())]))
        print('cur step:\t\t{}'.format(self.cur_step))
        print('cur timestamp:\t{}'.format(self.cur_timestamp))
        print('state:\t\t\t{}'.format(self.state))
        print('rate:\t\t\t{}'.format(self.rate))
        print('chance:\t\t\t{}'.format(self.chance))
        print('staff_cnt:\t\t{}'.format(self.staff_cnt))
        print('govs_cnt:\t\t{}'.format(self.govs_cnt))
        print('terrors_cnt:\t{}'.format(self.terrors_cnt))
        print('no_one_cnt:\t\t{}'.format(self.no_one_cnt))

