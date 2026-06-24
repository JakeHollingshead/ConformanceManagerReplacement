import os
from flask import Blueprint, render_template, request, redirect, url_for, session

auth_bp = Blueprint('auth', __name__)

APP_USERNAME = os.getenv("APP_USERNAME", "ISO")
APP_PASSWORD = os.getenv("APP_PASSWORD", "A123456!")


@auth_bp.before_app_request
def require_login():
    if request.endpoint not in ('auth.login', 'auth.logout', 'static') and 'user' not in session:
        return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if (request.form.get('username') == APP_USERNAME and
                request.form.get('password') == APP_PASSWORD):
            session['user'] = APP_USERNAME
            return redirect(url_for('home.home'))
        error = 'Invalid username or password.'
    return render_template('login.html', error=error)


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
