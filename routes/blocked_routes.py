from flask import Blueprint, render_template

blocked_bp = Blueprint('blocked', __name__)

@blocked_bp.route('/blocked', methods=['GET'])
def blocked():
    return render_template('blocked.html')
