from .routes import reactor_blueprint
from flask import Flask
from flask import current_app
import yaml
from . import db
import os

this_root = os.path.split(__file__)[0]

def load_yaml(path):
    with open(file=path, mode='r') as f:
        data = yaml.load(f)
    return data

def init_app(app):
    """
    1) load keys
    2) set secret key
    3) check db tables - if not exist create
    """
    app.configs = load_yaml(os.path.join(os.path.split(__file__)[0], 'configs.yaml'))
    app.secret_key = app.configs['secret']
    db.init(app)


def create_app():
    app = Flask(__name__,
                static_folder='static',
                template_folder='templates'
                )
    init_app(app)
    app.register_blueprint(reactor_blueprint, url_prefix='')
    return app


def run_app(port, host, debug):
    app = create_app()
    app.run(host, port, debug)


def run_debug():
    run_app(port=5000, host='localhost', debug=True)


def run_prod():
    run_app(port=5000, host='0.0.0.0', debug=False)
