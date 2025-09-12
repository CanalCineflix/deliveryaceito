from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import current_user, login_required

# Cria o Blueprint
blocked_bp = Blueprint('blocked', __name__)

@blocked_bp.route('/blocked')
@login_required
def blocked():
    """
    Renderiza a página que informa ao usuário que o acesso está bloqueado.
    O usuário é redirecionado para esta página se o plano dele estiver expirado.
    """
    if current_user.is_authenticated and current_user.has_active_plan():
        # Se o usuário tiver um plano ativo, redirecione para o dashboard
        flash('Seu plano está ativo! Bem-vindo(a) de volta.', 'success')
        return redirect(url_for('dashboard.index'))
        
    return render_template('blocked.html')
