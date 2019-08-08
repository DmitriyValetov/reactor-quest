from datetime import datetime
import time
import random
# import matplotlib.pyplot as plt
import sqlite3
import json
from pprint import pprint

from app.events import factory, terrors_factory, staff_factory, govs_factory


class Reactor:
    def __init__(self, step=1, work=120, chance_rate=0.05, rate_factor=1):
        self.step = step  # state update period in seconds
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
        self.db = None  # database path
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

    def run(self, plot=True, simulate=False,
            simulate_teams=None, last_dump=False):
        if plot:
            self.create_plot()
        while len(self.ts) < self.work:
            if simulate:
                self.simulate(simulate_teams)
            time.sleep(self.step)  # wait for the next step
            self.update()
            if last_dump:
                if len(self.ts) == self.work:
                    self.dump()
            else:
                self.dump()
            if plot:
                self.plot()

    def run_db(self, db, plot=True, reset_db=True,
               simulate=True, simulate_teams=None, last_dump=False):
        self.db = db
        if reset_db:
            self.reset_db()
        else:  # load last state
            self.load_db()
        self.run(plot, simulate, simulate_teams, last_dump)

    def update(self):
        self.ts.append(datetime.utcnow())
        self.queue = []
        # update events queue
        if self.db is not None:
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
        if self.db is not None:
            self.dump_db()
        else:
            pass  # TODO non db dump

    def simulate(self, simulate_teams=None):
        if simulate_teams is None:
            simulate_teams = ['staff', 'terrors', 'govs']
        staff_name = random.choice(list(staff_factory))
        terrors_name = random.choice(list(terrors_factory))
        govs_name = random.choice(list(govs_factory))
        if self.state > 150:
            staff_event = {'name': 'scram', 'work': 1, 'source': 'staff'}
        else:
            staff_event = {'name': staff_name, 'work': 1, 'source': 'staff'}
        terrors_event = {'name': terrors_name, 'work': 1, 'source': 'terrors'}
        govs_event = {'name': govs_name, 'work': 1, 'source': 'govs'}
        staff_event_json = json.dumps(staff_event)
        terrors_event_json = json.dumps(terrors_event)
        govs_event_json = json.dumps(govs_event)
        events_json = list()
        if 'staff' in simulate_teams:
            events_json.append(staff_event_json)
        if 'terrors' in simulate_teams:
            events_json.append(terrors_event_json)
        if 'govs' in simulate_teams:
            events_json.append(govs_event_json)
        if self.db is not None:
            con = sqlite3.connect(self.db)
            try:
                cur = con.cursor()
                cur.executemany('INSERT INTO events VALUES (?, ?)',
                                [(None, x) for x in events_json])
                con.commit()
            except Exception as e:
                print(e)
            finally:
                con.close()
        else:
            pass  # TODO non db simulation

    def update_events_local(self):
        if 0 < self.state < 50:
            self.queue.append(
                {'name': 'iodine', 'work': 1, 'source': 'reactor'})
        if random.uniform(0, 1) < self.chance:
            self.queue.append({'name': 'boom', 'work': 1, 'source': 'reactor'})

    def update_events_db(self):
        # add local events to db
        local_events_json = []
        if 0 < self.state < 50:
            local_events_json.append(json.dumps(
                {'name': 'iodine', 'work': 1, 'source': 'reactor'}))
        if random.uniform(0, 1) < self.chance:
            local_events_json.append(json.dumps(
                {'name': 'boom', 'work': 1, 'source': 'reactor'}))
        # db
        con = sqlite3.connect(self.db)
        try:
            cur = con.cursor()
            cur.executemany('INSERT INTO events VALUES (?, ?)',
                            [(None, x) for x in local_events_json])
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
        # state.pop('grid', None)  # from colab plot
        state_json = json.dumps(
            state,
            default=lambda x: x.isoformat() if isinstance(x, datetime) else x)
        con = sqlite3.connect(self.db)
        try:
            cur = con.cursor()
            cur.execute('INSERT INTO states VALUES (?, ?)', [None, state_json])
            con.commit()
        except Exception as e:
            print(e)
        finally:
            con.close()

    def load_db(self):
        con = sqlite3.connect(self.db)
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
        con = sqlite3.connect(self.db)
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
        pass
        # self.grid = widgets.Grid(3, 2, header_row=True, header_column=True)

    def plot(self):
        print('\nstep: {}'.format(len(self.ts)))
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
        print('\n'.join(['{:^4}|{:^10}|{:^20}|'.format(i + 1, x['source'], x['name'])
                         for i, x in enumerate(self.queue)]))
        print('scores')
        print('terrors: {}'.format(-1*self.boom_cnt))
        print('staff: {}'.format(-1*self.max_safe_steps + 0.4*self.zero_cnt))
        print('govs: {}'.format(-4*self.produced/1000 + 1.4*self.boom_cnt))
        # with self.grid.output_to(0, 0):
        #     self.grid.clear_cell()
        #     plt.figure(figsize=(3, 2))
        #     plt.xlabel('time')
        #     plt.ylabel('%')
        #     plt.title('State')
        #     plt.plot(self.ts, self.ss, 'o-r')
        #     # fig.plot(self.ts, self.ss, 'o-r')
        # with self.grid.output_to(0, 1):
        #     self.grid.clear_cell()
        #     plt.figure(figsize=(3, 2))
        #     plt.xlabel('time')
        #     plt.ylabel('energy')
        #     plt.title('Produced')
        #     plt.plot(self.ts, self.ps, 'o-g')
        # with self.grid.output_to(1, 0):
        #     self.grid.clear_cell()
        #     plt.figure(figsize=(3, 2))
        #     plt.xlabel('time')
        #     plt.ylabel('state per step')
        #     plt.title('Rate')
        #     plt.plot(self.ts, self.rs, 'o-b')
        # with self.grid.output_to(1, 1):
        #     self.grid.clear_cell()
        #     plt.figure(figsize=(3, 2))
        #     plt.xlabel('time')
        #     plt.ylabel('rate per step')
        #     plt.title('Acceleration')
        #     plt.plot(self.ts, self.acs, 'o-y')
        # with self.grid.output_to(2, 0):
        #     self.grid.clear_cell()
        #     plt.figure(figsize=(3, 2))
        #     plt.xlabel('time')
        #     plt.ylabel('%')
        #     plt.title('Disaster chance')
        #     plt.plot(self.ts, self.cs, 'o-m')
        # with self.grid.output_to(2, 1):
        #     plt.figure(figsize=(3, 2))
        #     self.grid.clear_cell()
        #     print('start: {}'.format(self.ts[0].strftime('%H:%M:%S')))
        #     print('current: {}'.format(self.ts[-1].strftime('%H:%M:%S')))
        #     print('step: {}'.format(len(self.ts)))
        #     print('scrams: {}'.format(self.scram_cnt))
        #     print('booms: {}'.format(self.boom_cnt))
        #     print('zeros: {}'.format(self.zero_cnt))
        #     print('anti-terrorist operations: {}'.format(self.ato_cnt))
        #     print('safe steps: {}'.format(self.safe_cnt))
        #     print('max safe steps: {}'.format(self.max_safe_steps))
        #     print('produced: {}'.format(self.produced))
        #     for e in self.queue:
        #         print('name: {}, source: {}'.format(e['name'], e['source']))
