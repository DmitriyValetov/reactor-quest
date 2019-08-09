import yaml
from pprint import pprint

from app.reactor import Reactor

if __name__ == '__main__':
    with open('app/configs_reactor.yaml') as f:
        cfg = yaml.load(f, Loader=yaml.FullLoader)
    pprint(cfg)
    r = Reactor(**cfg['reactor'])
    r.run(**cfg['run'])
