from sqlalchemy import Table, Column, Integer, ForeignKey, String, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sqlite3
import os

root = os.path.split(__file__)[0]
Base = declarative_base()

class State(Base):
    __tablename__ = 'states'
    id = Column(Integer, primary_key=True, autoincrement=True)
    data = Column(String)
    def __repr__(self):
        return "State ({} : {} : {})".format(self.id, self.name, self.ap)
        
class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True, autoincrement=True)
    data = Column(String)
    def __repr__(self):
        return "Event ({} : {} : {})".format(self.id, self.name, self.ap)

class Team(Base):
    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    ap = Column(Integer) # action points
    def __repr__(self):
        return "Team ({} : {} : {})".format(self.id, self.name, self.ap)

class PromoAct(Base):
    __tablename__ = 'PromoActs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String)
    team = relationship("Team")
    def __repr__(self):
        return "PromoAct ({} : {} : {})".format(self.id, self.name, self.team)

def check_Promoact(promo_code, team_name):
    engine = create_engine('sqlite:///{}'.format(os.path.join(root, 'reactor.db')))
    Session = sessionmaker(bind=engine)
    session = Session()
    session.add(PromoAct(name=hesouam, team=))
    print('\n\n')
    print(session.query(PromoAct.id).filter_by(code=promo_code).get(0))
    print('\n\n')
    promo_used = session.query(PromoAct.id).filter_by(code=promo_code).filter(PromoAct.team.has(name=team_name)).scalar() is not None
    session.commit()
    session.close()
    engine.dispose()
    return promo_used

def increment_ap(team_name, incr_ap):
    engine = create_engine('sqlite:///{}'.format(os.path.join(root, 'reactor.db')))
    Session = sessionmaker(bind=engine)
    session = Session()
    team_obj = session.query(Team).filter_by(name=team_name).get(1)
    team_obj.ap += incr_ap
    session.commit()
    session.close()
    engine.dispose()

def add_PromoAct(promo_code, team_name):
    engine = create_engine('sqlite:///{}'.format(os.path.join(root, 'reactor.db')))
    Session = sessionmaker(bind=engine)
    session = Session()
    session.add(PromoAct(code=promo_code, team=team_name))
    session.commit()
    session.close()
    engine.dispose()

def init(app):
    """
    Initialize db sheme
    """
    engine = create_engine('sqlite:///{}'.format(os.path.join(root, 'reactor.db')))
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    for team_name in app.configs['teams']:
        team_exists = session.query(Team.id).filter_by(name=team_name).scalar() is not None
        if not(team_exists):
            new_team = Team(name=team_name, ap=app.configs['init_ap'])
            session.add(new_team)
    session.commit()
    session.close()
    engine.dispose()
    
def clear():
    engine = create_engine('sqlite:///{}'.format(os.path.join(root, 'reactor.db')))
    Session = sessionmaker(bind=engine)
    session = Session()
    session.Event.query().delete()
    session.State.query().delete()
    session.Team.query().delete()
    session.close()
    engine.dispose()
    
def drop_tables():
    engine = create_engine('sqlite:///{}'.format(os.path.join(root, 'reactor.db')))
    Event.__table__.drop(engine)
    State.__table__.drop(engine)
    Team.__table__.drop(engine)
    engine.dispose()

def init_solutons_db_sheme():
    engine = create_engine('sqlite:///{}'.format(os.path.join(root, 'reactor.db')))
    Base.metadata.create_all(engine)
    engine.dispose()

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

def init_db(path):
    """
    Init or drop reactor.db
    There should be tables: states, events, teams
    """
    # clear tables
    con = sqlite3.connect(os.path.join(path, 'reactor.db'))
    cur = con.cursor()
    cur.execute('''DROP TABLE IF EXISTS states''')
    cur.execute('''CREATE TABLE IF NOT EXISTS states (
    id integer PRIMARY KEY, data text)''')
    cur.execute('''DROP TABLE IF EXISTS events''')
    cur.execute('''CREATE TABLE IF NOT EXISTS events (
    id integer PRIMARY KEY, data text)''')
    con.close()

def check_tables(path):
    """
    Check if tables exists: states, events, teams - create them
    """
    check_string = "SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';"
    create_string = "CREATE TABLE IF NOT EXISTS {table_name} (id integer PRIMARY KEY, data text)"
    with sqlite3.connect('./reactor.db') as con:
        cur = con.cursor()
        tables = ['states', 'events']
        for tbl in tables:
            formated_check_string = check_string.format(tbl)
            cur.execute(formated_check_string)
            if cur.fetchone() is None:
                cur.execute(create_string.format(tbl))
