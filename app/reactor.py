from datetime import datetime
import time
# import matplotlib.pyplot as plt
import sqlite3
import json
# import numpy as np
import os

from app.events import factory, staff_factory, terrors_factory, govs_factory
from app.strategies import strategy_factory


class Reactor:
    def __init__(self, step=1, work=120, chance_rate=0.05, rate_factor=1,
                 reactor_strategy='reactor_1'):
        self.step = step  # state update period in seconds
        self.cur_step = 0
        self.cur_timestamp = None
        self.work = work  # working time in steps
        self.state = 0  # state [0, 100) (energy produced per step, max 100)
        self.rate = 0  # state rate per step
        self.rate_factor = rate_factor  # rate factor (manually determined)
        self.acc = 0  # state acceleration per step
        self.produced = 0  # total energy produced
        self.queue = []  # queue of current step events
        self.events_state = {}  # db events states (check time of working)
        self.chance = 0  # boom chance for states > 100 (checked every step)
        self.chance_rate = chance_rate  # chance rate per step for states > 100
        self.scram_cnt = 0  # number of scram uses
        self.boom_cnt = 0  # number of booms
        self.ato_cnt = 0  # number of anti-terrorist operations
        self.safe_cnt = 0  # steps after 0 state counter (for max_safe_steps)
        self.zero_cnt = 0  # number of 0 states
        self.over_cnt = 0  # number of 1+ states
        self.max_safe_steps = 0  # steps between 0 states
        self.ts = []  # times history by steps
        self.ss = []  # states history
        self.rs = []  # rates history
        self.acs = []  # accelerations history
        self.ps = []  # energy produced history
        self.cs = []  # disaster chances history
        self.dump_path = 'reactor.json'  # file or db path
        self.db = False  # dump to db?
        self.reactor_strategy = 'reactor_1'

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
        while len(self.ts) < self.work:
            self.queue = []
            if simulate:
                self.simulate(simulate_teams, simulate_strats)
            time.sleep(self.step)  # wait for the next step
            self.update()
            if last_dump:
                if len(self.ts) == self.work:
                    self.dump()
            else:
                self.dump()
            if plot:
                self.plot()

    def update(self):
        self.cur_step += 1
        self.cur_timestamp = datetime.utcnow()
        self.ts.append(self.cur_timestamp)
        # update events queue
        if self.db:
            self.update_events_db()
        else:
            self.update_events_local()
        # run events queue
        for e in self.queue:
            factory[e['name']](self)
        # update states and rate
        self.rate += 0.5 * self.acc * self.rate_factor
        self.state += self.rate
        self.rate += 0.5 * self.acc * self.rate_factor
        if 0 < self.state <= 100:
            self.produced += self.state
            self.chance -= self.chance_rate
            if self.chance < 0:
                self.chance = 0
            self.safe_cnt += 1
        elif self.state <= 0:
            self.state = 0
            self.rate = 0
            self.chance -= self.chance_rate
            if self.chance < 0:
                self.chance = 0
            self.safe_cnt = 0
            self.zero_cnt += 1
        else:  # self.state > 100
            self.produced += 100
            k = self.state / 100
            self.chance += k * self.chance_rate
            self.safe_cnt += 1
            self.over_cnt += 1
        self.max_safe_steps = max(self.safe_cnt, self.max_safe_steps)
        # update history
        self.ss.append(self.state)
        self.rs.append(self.rate)
        self.acs.append(self.acc)
        self.ps.append(self.produced)
        self.cs.append(self.chance)

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
                cur.executemany('INSERT INTO events VALUES (?, ?)',
                                [(None, json.dumps(x)) for x in events])
                con.commit()
            except Exception as e:
                print(e)
            finally:
                con.close()
        else:
            self.queue.extend(events)

    def update_events_local(self):
        events = strategy_factory[self.reactor_strategy](self, 'reactor')
        self.queue.extend(events)

    def update_events_db(self):
        events = strategy_factory[self.reactor_strategy](self, 'reactor')
        con = sqlite3.connect(self.dump_path)
        try:
            cur = con.cursor()
            cur.executemany('INSERT INTO events VALUES (?, ?)',
                            [(None, json.dumps(x)) for x in events])
            con.commit()
            events_json = cur.execute('''SELECT * FROM events''').fetchall()
        except Exception as e:
            print(e)
        else:
            for e in events_json:
                rowid, event_json = e
                self.events_state[str(rowid)] = self.events_state.setdefault(
                    str(rowid), 0) + 1
                # print(rowid, event_json, self.events_state[rowid])
                event = json.loads(event_json)
                if self.events_state[str(rowid)] <= event.get('work', 1):
                    self.queue.append(event)
        finally:
            con.close()

    def dump_db(self):
        state = self.__dict__.copy()
        state.pop('grid', None)  # from colab plot
        state_json = json.dumps(
            state,
            default=lambda x: x.isoformat() if isinstance(x, datetime) else x)
        con = sqlite3.connect(self.dump_path)
        try:
            cur = con.cursor()
            cur.execute('INSERT INTO states VALUES (?, ?)', [None, state_json])
            con.commit()
        except Exception as e:
            print(e)
        finally:
            con.close()

    def dump_json(self):
        state = self.__dict__.copy()
        state.pop('grid', None)  # from colab plot
        with open(self.dump_path, 'w') as f:
            json.dump(state, f, default=lambda x: x.isoformat()
            if isinstance(x, datetime) else x)

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
            for i, t in enumerate(last_state['ts']):
                last_state['ts'][i] = datetime.strptime(
                    t, "%Y-%m-%dT%H:%M:%S.%f")
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
          (id INTEGER PRIMARY KEY, data TEXT)''')
        except Exception as e:
            print(e)
        finally:
            con.close()

    def create_plot(self):
        # self.grid = widgets.Grid(3, 2, header_row=True, header_column=True)
        pass

    def plot(self):
        print('\nstep: {}'.format(len(self.ts)))
        print('cur step: {}'.format(self.cur_step))
        print('start: {}'.format(self.ts[0].strftime('%H:%M:%S')))
        print('current: {}'.format(self.ts[-1].strftime('%H:%M:%S')))
        print('scrams: {}'.format(self.scram_cnt))
        print('booms: {}'.format(self.boom_cnt))
        print('zeros: {}'.format(self.zero_cnt))
        print('overs: {}'.format(self.over_cnt))
        print('atos: {}'.format(self.ato_cnt))
        print('safe steps: {}'.format(self.safe_cnt))
        print('max safe steps: {}'.format(self.max_safe_steps))
        print('state: {}'.format(self.ss[-1]))
        print('rate: {}'.format(self.rs[-1]))
        print('acc: {}'.format(self.acs[-1]))
        print('produced: {}'.format(self.ps[-1]))
        print('chance: {}'.format(self.cs[-1]))
        print('{:^4}|{:^10}|{:^20}|'.format('n', 'source', 'event'))
        print('-'.join(['' for _ in range(38)]))
        print('\n'.join(
            ['{:^4}|{:^10}|{:^20}|'.format(i + 1, x['source'], x['name'])
             for i, x in enumerate(self.queue)]))
        print('scores')
        print('terrors: {}'.format(-1 * self.boom_cnt))
        print('staff: {}'.format(
            -1 * self.max_safe_steps + 0.4 * self.zero_cnt))
        print('govs: {}'.format(
            -4 * self.produced / 1000 + 1.4 * self.boom_cnt))
