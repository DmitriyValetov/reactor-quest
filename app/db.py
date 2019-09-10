from sqlalchemy import Table, Column, Integer, ForeignKey, String, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime
import sqlite3
import json
import yaml
import os

root = os.path.split(__file__)[0]
Base = declarative_base()

def make_engine():
    return create_engine('sqlite:///{}'.format(os.path.join(root, 'reactor.db')))

class State(Base):
    __tablename__ = 'states'
    id = Column(Integer, primary_key=True, autoincrement=True)
    data = Column(String)
    def __repr__(self):
        return "State ({} : {})".format(self.id, self.data)

class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True, autoincrement=True)
    data = Column(String)
    status = Column(Integer)
    start = Column(Integer)
    end = Column(Integer)
    def __repr__(self):
        return "Event ({} : {} : {} : {} : {} : {})".format(
            self.id, self.name, self.ap, self.status, self.start, self.end)

class Team(Base):
    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True)
    ap = Column(Integer) # action points
    last_cast_time = Column(DateTime)
    promos = relationship('Promo')
    def __repr__(self):
        return "Team ({} : {} : {})".format(self.id, self.name, self.ap)

class Promo(Base):
    __tablename__ = 'promos'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    status = Column(String, default='off')
    team_id = Column(Integer, ForeignKey('teams.id'))
    ap = Column(Integer) # action points
    def __repr__(self):
        return "Promo ({} : {} : {} : {})".format(self.id, self.name, self.status, self.team_id)


def get_info():
    """
    returns some db info
    """
    engine = make_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    data = {'promos':[], 'teams':[]}
    for team in session.query(Team).all():
        data['teams'].append(str(team))
    for promo in session.query(Promo).all():
        data['promos'].append(str(promo))
    session.commit()
    session.close()
    engine.dispose()
    return json.dumps(data)

def promo_exists(promo_code, team_name):
    """
    None - promo is no suitable for this comand
    False - promo not used
    True - promo already used
    """
    engine = make_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    promo = (session.query(Promo)
                    .join(Team)
                    .filter(Team.id == Promo.team_id)
                    .filter(Team.name == team_name)
                    .filter(Promo.name == promo_code)
                    .first())

    # session.commit() # no changes!
    session.close()
    engine.dispose()
    return promo is not None

def promo_was_used(promo_name, team_name):
    """
    None - promo is no suitable for this comand
    False - promo not used
    True - promo already used
    """
    engine = make_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    promo_used = None
    promos = session.query(Team).filter(Team.name == team_name).one().promos
    for p in promos:
        if p.name == promo_name:
            if p.status == 'off':
                promo_used = False
            else:
                promo_used = True

    # session.commit() # no changes!
    session.close()
    engine.dispose()
    return promo_used

def increment_ap(team_name, incr_ap):
    engine = make_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    team_obj = session.query(Team).filter_by(name=team_name).first()
    team_obj.ap += incr_ap
    session.add(team_obj)
    session.commit()
    session.close()
    engine.dispose()

def team_not_in_cooldown(team_name):
    engine = make_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        answer = False
        team = session.query(Team).filter_by(name=team_name).first()
        if team.last_cast_time is None or datetime.datetime.today() - team.last_cast_time > datetime.timedelta(0, 1*60, 0):
            answer = True
    except BaseException as e:
        raise e
    finally:
        # session.commit()
        session.close()
        engine.dispose()
    return answer

def toggle_promo(promo_name, team_name):
    """
    False - toggle failed
    True - toggle success
    """
    engine = make_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    ap_value = None
    promo_toggled = False
    team = session.query(Team).filter(Team.name == team_name).first()
    promos = team.promos
    for p in promos:
        if p.name == promo_name:
            if p.status == 'off':
                p.status = 'on'
                team.last_cast_time = datetime.datetime.today()
                promo_toggled = True
                ap_value = p.ap
                session.add(p)

    session.commit()
    session.close()
    engine.dispose()
    return promo_toggled, ap_value

def get_team_ap(team_name):
    engine = make_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    team_ap = None
    try:
        team_obj = session.query(Team).filter_by(name=team_name).first()
        team_ap = team_obj.ap
    except BaseException as e:
        raise e
    finally:
        # session.add(team_obj)
        # session.commit() # no changes !!!
        session.close()
        engine.dispose()
    return team_ap

def restore_promos():
    engine = make_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    for p in session.query(Promo).all():
        p.status = 'off'
        session.add(p)
    session.commit()
    session.close()
    engine.dispose()

def null_teams_aps():
    engine = make_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    for t in session.query(Team).all():
        t.ap = 0
        session.add(t)
    session.commit()
    session.close()
    engine.dispose()

def init(app):
    """
    Initialize db sheme
    """
    engine = make_engine()
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    for team_name in app.configs['teams']:
        team_exists = session.query(Team.id).filter_by(name=team_name).scalar() is not None
        if not(team_exists):
            new_team = Team(name=team_name, ap=app.configs['init_ap'])
            if team_name in app.configs['promos']:
                for promo_pack in app.configs['promos'][team_name]:
                    new_team.promos.append(Promo(name=promo_pack['name'], status='off', ap=promo_pack['ap']))
            session.add(new_team)
    session.commit()
    session.close()
    engine.dispose()

def clear():
    engine = make_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    session.Event.query().delete()
    session.State.query().delete()
    session.Team.query().delete()
    session.close()
    engine.dispose()

def drop_tables():
    engine = make_engine()
    Event.__table__.drop(engine)
    State.__table__.drop(engine)
    Team.__table__.drop(engine)
    engine.dispose()

def init_solutons_db_sheme():
    engine = make_engine()
    Base.metadata.create_all(engine)
    engine.dispose()

def add_action_to_db(name, source):
    engine = make_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    new_event = Event(data=json.dumps({'name': name, 'source': source}),
                      status=1)
    session.add(new_event)
    session.commit()
    session.close()
    engine.dispose()

def get_stats_by_parameter_name(parameter_name):
    """
    extract state data from db by parameter_name  
    """
    engine = make_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    data = {'x':[], 'y':[]}
    # for i, state in enumerate(session.query(State).all()[-6:]):
    limit = 6
    for i, state in enumerate(session.query(State).order_by(State.id.desc()).limit(limit)):
        state_dict = yaml.load(state.data)
        data['x'].append(i*state_dict['step'])
        data['y'].append(state_dict[parameter_name])
    data['y'].sort(reverse=True)
    session.close()
    engine.dispose()
    return data

def get_stats_by_configs(configs, login):
    if login not in configs['plots_access']:
        raise ValueError('No such login in plots configs: {}'.format('plots_access'))
    
    engine = make_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    data = {
            'scalars': {s_p_name: None for s_p_name in configs['plots_access'][login]['scalars']}, 
            'time_series': {ts_p_name: {'x': [], 'y': []} for ts_p_name in configs['plots_access'][login]['time_series']}
            }
    states = session.query(State).order_by(State.id.desc()).limit(configs.get('points_amount', 5)).all()
    if len(states) == 0:
        return {}

    for i, state in reversed(list(enumerate(states))):
        state_dict = yaml.load(state.data)
        for time_series_name in configs['plots_access'][login]['time_series']:
            # data['time_series'][time_series_name]['x'].append(i*state_dict['step'])
            data['time_series'][time_series_name]['x'].append(state_dict['cur_timestamp'])
            data['time_series'][time_series_name]['y'].append(state_dict[time_series_name])
    

    # for time_series_name in configs['plots_access'][login]['time_series']:       
    #    data['time_series'][time_series_name]['y'] = data['time_series'][time_series_name]['y'].reverse()
    #    data['time_series'][time_series_name]['x'] = data['time_series'][time_series_name]['x'].reverse()
    
    for scalar_name in configs['plots_access'][login]['scalars']:       
       data['scalars'][scalar_name] = yaml.load(states[0].data)[scalar_name]
    
    session.close()
    engine.dispose()

    return data

# def target_data_db_func(root):
#     engine = create_engine('sqlite:///{}'.format(os.path.join(root, "solutions.sqlite")), echo=True)
#     Session = sessionmaker(bind=engine)
#     session = Session()
#     solution_packs = session.query(SolutionPack).all()
#     x = []
#     y = []
#     for pack in solution_packs:
#         values = []
#         for sol in pack.solutions:
#             values.append(sol.value)

#         x.append(pack.modelRunInfo)
#         y.append(min(values))
#     session.close()
#     engine.dispose()
#     return x, y

# def init_db(path):
#     """
#     Init or drop reactor.db
#     There should be tables: states, events, teams
#     """
#     # clear tables
#     con = sqlite3.connect(os.path.join(path, 'reactor.db'))
#     cur = con.cursor()
#     cur.execute('''DROP TABLE IF EXISTS states''')
#     cur.execute('''CREATE TABLE IF NOT EXISTS states (
#     id integer PRIMARY KEY, data text)''')
#     cur.execute('''DROP TABLE IF EXISTS events''')
#     cur.execute('''CREATE TABLE IF NOT EXISTS events (
#     id integer PRIMARY KEY, data text)''')
#     con.close()

# def check_tables(path):
#     """
#     Check if tables exists: states, events, teams - create them
#     """
#     check_string = "SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';"
#     create_string = "CREATE TABLE IF NOT EXISTS {table_name} (id integer PRIMARY KEY, data text)"
#     with sqlite3.connect('./reactor.db') as con:
#         cur = con.cursor()
#         tables = ['states', 'events']
#         for tbl in tables:
#             formated_check_string = check_string.format(tbl)
#             cur.execute(formated_check_string)
#             if cur.fetchone() is None:
#                 cur.execute(create_string.format(tbl))
