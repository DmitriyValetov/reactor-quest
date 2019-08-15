from flask import Flask, request, render_template, redirect, url_for, session
from flask import Blueprint
from flask import current_app, send_file
import hashlib
import json
from . import db

no_login_check_routes = [
    'reactor.get_teams_promos_info', # /info
    'reactor.null_teams_aps',        # /null_teams_aps
    'reactor.restore_promos',        # /restore_promos
    'reactor.configs',               # /configs
    'reactor.ajax_login'
]


reactor_blueprint = Blueprint(
    name = 'reactor',
    import_name = __name__,
)


def compare_passwords(real_hash, income_pass):
    m = hashlib.sha512()
    m.update(str(income_pass).encode('ascii') + 'salt'.encode('ascii'))
    income_hash = m.hexdigest()
    return real_hash == income_hash

@reactor_blueprint.before_request
def before_request():
    print('before-request entered before: ', request.endpoint)
    if request.endpoint in no_login_check_routes:
        return # login unnecessary
    if not( ('login' in session) and ('pass' in session) and compare_passwords(str(current_app.configs['auth'][session['login']]), session['pass']) ):
        if 'login' in session: del session['login']
        if 'pass' in session: del session['pass']
        if request.endpoint != 'reactor.login':
            return redirect(url_for('reactor.login'))

@reactor_blueprint.route('/', methods=['GET', 'POST'])
def login():
    """
    login page
    """
    return render_template('login.html')


@reactor_blueprint.route('/main', methods=['GET', 'POST'])
def main():
    """
    main page
    """
    if request.method == 'POST' and 'action' in request.form:
        action = request.form['action']
        if action == 'exit':
            del session['login']
            del session['pass']
            return redirect(url_for('reactor.login'))
        elif action == 'topromo':
            return redirect(url_for('reactor.promo'))
        elif action == 'tocontrols':
            return redirect(url_for('reactor.controls'))
        elif action == 'todashboard':
            return redirect(url_for('reactor.dash_board'))

    team_name = session['login']
    team_ap = db.get_team_ap(session['login'])
    return render_template('main.html', team_name=team_name, team_ap=team_ap)

@reactor_blueprint.route('/admin', methods=['GET', 'POST'])
def admin():
    """
    main page
    """
    return render_template('admin.html')

@reactor_blueprint.route('/controls', methods=['GET', 'POST'])
def controls():
    """
    main page
    """
    return render_template('controls.html', team_name=session['login'])

@reactor_blueprint.route('/promo', methods=['GET', 'POST'])
def promo():
    """
    main page
    """
    return render_template('promo.html', team_name=session['login'])

@reactor_blueprint.route('/dash_board', methods=['GET', 'POST'])
def dash_board():
    """
    main page
    """
    return render_template('dash_board.html')

#===================================================================================
#==========================   for ajax requests   ==================================
#===================================================================================

@reactor_blueprint.route('/configs', methods=['GET', 'POST'])
def configs():
    """
    main page
    """
    return json.dumps(current_app.configs)

@reactor_blueprint.route('/restore_promos', methods=['GET', 'POST'])
def restore_promos():
    db.restore_promos()
    return json.dumps({'status': 200, 'data': 'Success with: setting `off` status to all promos'})


@reactor_blueprint.route('/null_teams_aps', methods=['GET', 'POST'])
def null_teams_aps():
    db.null_teams_aps()
    return  json.dumps({'status': 200, 'data': 'Success with: setting 0 ap to all teams.'})


@reactor_blueprint.route('ajax/toggle_promo', methods=['GET'])
def toggle_promo():
    """
    TODO - add time cooldown for 1 minute
    """
    if 'promo' not in request.args:
        return json.dumps({'status': 400, 'data': 'No promo key/value in request.'})

    team_name = session['login']
    responce_msg = None
    responce_status = 200
    team_ap_is = db.get_team_ap(team_name)

    promo_code = request.args['promo']
    if not db.promo_exists(promo_code, team_name):
        responce_msg = "Промо {} не существует.".format(promo_code)
    elif not db.promo_was_used(promo_code, team_name):
        if db.team_not_in_cooldown(team_name):
            success, ap_value = db.toggle_promo(promo_code, team_name)
            if success:
                db.increment_ap(team_name, ap_value)
                team_ap_is = db.get_team_ap(team_name)
                responce_msg = "Промо активировано. Текущие очки команды {} - {}".format(team_name, team_ap_is)
        else:
            responce_msg = "Пожалуйста, попробуйте через минуту. Сервер горит."
    else:
        responce_msg = "Это промо уже было активировано вашей командой :)"

    return  json.dumps({'status': responce_status, 'data': responce_msg, 'current_ap': team_ap_is})


@reactor_blueprint.route('/info', methods=['GET'])
def get_teams_promos_info():
    return db.get_info()

@reactor_blueprint.route('ajax/team_ap', methods=['GET'])
def get_team_ap():
    # team_ap = db.get_team_ap(session['login'])        # ok, but I want to excersice with 
    team_ap = db.get_team_ap(request.args['team_name']) # get request and args
    return json.dumps({'status': 200, 'data': {'team_ap': team_ap}})

@reactor_blueprint.route('ajax/login', methods=['POST'])
def ajax_login():
    """
    1) is password in the request.form?
    2) if it matches to one in the configs with salt and been hashed (all passwords are unique, lol):
            2.1) add to session the login
            2.2) return success (client will try to go enter /main page)
        else:
            2.3) return fail
    """
    if 'password' not in request.form:
        return json.dumps({'status': 400, 'data': 'No pass key in submitted form'})

    return_dict = {}
    password = request.form['password']
    for role in current_app.configs['auth'].keys():
        if compare_passwords(str(current_app.configs['auth'][role]), password):
            session['login'] = role
            session['pass'] = password
            return_dict = {'status': 200, 'data': 'Вход упешен. Ваша команда: {}'.format(session['login'])}
            break
        else:
            return_dict = {'status': 452, 'data': 'Нет команды с таким паролем. Попробуйте ещё раз меня хакнуть.'}

    return json.dumps(return_dict)

@reactor_blueprint.route('ajax/available_actions', methods=['GET'])
def available_actions():
    if 'team_name' not in request.args:
        return json.dumps({'status': 400, 'data': 'No team_name key/value in request.'})

    team_name = request.args['team_name']
    actions = filter(lambda x: x['access'] is None or team_name in x['access'], current_app.configs['actions'])
    actions = map(lambda x: {'name': x['name'], 'cost': x['cost']}, actions)
    actions = list(actions)
    return json.dumps({'status': 200, 'data': {'actions': actions}})

@reactor_blueprint.route('ajax/push_action', methods=['POST'])
def push_team_action():
    print(request.form)
    if 'action_name' not in request.form or 'team_name' not in request.form:
        return json.dumps({'status': 400, 'data': 'No team_name or action_name key/value in request.'})

    action_name = request.form['action_name']
    team_name = request.form['team_name']
    team_ap = db.get_team_ap(team_name) # get request and args
    found_similar = list(filter(lambda x: x['name'] == action_name, current_app.configs['actions']))
    action_exists = len(found_similar) > 0
    found_action = found_similar[0]
    if not action_exists:
        return json.dumps({'status': 452, 'data': {'header': 'ОшЫбка', 'body': 'Нет такого действия({}) в списке на сервере... Ты меня хакаешь?'.format(action_name)}})
    if found_action['access'] is not None and team_name not in found_action['access']:
        return json.dumps({'status': 452, 'data': {'header': 'ОшЫбка', 'body': 'Эта команда({}) не имеет права на это действие({})... Ты меня хакаешь?'.format(team_name, action_name)}})
    if team_ap < found_action['cost']:
        return json.dumps({'status': 452, 'data': {'header': 'ОшЫбка', 'body': 'У этой команды({}) не хватает очков на это действие({})... Ты меня хакаешь?'.format(team_name, action_name)}})
    
    db.increment_ap(team_name, -found_action['cost'])
    db.add_action_to_db(name=action_name, work=found_action['work'], source=team_name)

    return json.dumps({'status': 200, 'data': {'header': 'Успешно!', 'body': '{} задействовало "{}"!'.format(team_name, action_name)}})


@reactor_blueprint.route('ajax/get_stats', methods=['GET'])
def get_stats():
    if 'parameter_name' not in request.args:
        return json.dumps({'status': 400, 'data': 'No parameter_name key/value in request.'})
    # data = {'x': [1,2,3], 'y': [1, 10, 100]}
    parameter_name = request.args['parameter_name']
    data = db.get_stats_by_parameter_name(parameter_name)
    return json.dumps({'status': 200, 'data': data})
