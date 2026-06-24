from flask import Blueprint, render_template

help_bp = Blueprint('help_page', __name__)


@help_bp.route('/Help')
def help_page():
    return render_template('Help.html')
