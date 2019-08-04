from flask import Flask, request, render_template, redirect, url_for, session
from flask import Blueprint
from flask import current_app
import hashlib
import json
from . import db


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
    if not( ('login' in session) and ('pass' in session) and compare_passwords(str(current_app.configs['auth'][session['login']]), session['pass']) ):
        if 'login' in session: del session['login']
        if 'pass' in session: del session['pass']
        if request.endpoint != 'reactor.login':
            return redirect(url_for('reactor.login'))
    print('Auth passed: {} at {} page'.format(session['login'], request.endpoint))

@reactor_blueprint.route('/', methods=['GET', 'POST'])
def login():
    """
    login page
    """
    print('login page entered')
    if ('login' in session) and ('pass' in session) and compare_passwords(str(current_app.configs['auth'][session['login']]), session['pass']):
        return redirect(url_for('reactor.main'), code=302)
    else:
        if 'login' in session: del session['login']
        if 'pass' in session: del session['pass']


    # check login
    if request.method == 'POST' and 'pass' in request.form:
        for role in current_app.configs['auth'].keys():
            if compare_passwords(current_app.configs['auth'][role], request.form['pass']):
                session['login'] = role
                session['pass'] = request.form['pass']
                if role == 'admin':
                    return redirect(url_for('reactor.admin'), code=302)  
                return redirect(url_for('reactor.main'), code=302)

    # return redirect(url_for('reactor.main'), code=302)
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

    return render_template('main.html')

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
    return render_template('controls.html')

@reactor_blueprint.route('/promo', methods=['GET', 'POST'])
def promo():
    """
    main page
    """
    if request.method == 'POST' and 'promo' in request.form:
        # promo exists:
        if str(request.form['promo']) in current_app.configs['promo']:
            # check promo code to be used already
            if db.check_Promoact(request.form['promo'], session['login']):
                db.increment_ap(session['login'], current_app.configs['promo'][request.form['promo']])
                db.add_PromoAct(request.form['promo'], session['login'])

    return render_template('promo.html')

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