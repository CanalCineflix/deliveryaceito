from flask import Blueprint, render_template

blocked_bp = Blueprint('blocked', __name__)

@blocked_bp.route('/blocked')
def blocked():
    return render_template('blocked.html')
