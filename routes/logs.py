from flask import Blueprint, render_template, request, abort
from flask_login import login_required, current_user
from models import OperationLog, User, db
from config import Config
from datetime import datetime

logs_bp = Blueprint('logs', __name__)


def get_operation_type_text(op_type):
    return Config.OPERATION_TYPES.get(op_type, op_type)


def get_badge_class(op_type):
    if op_type.startswith('asset_'):
        return 'badge-primary'
    elif op_type.startswith('borrow_'):
        return 'badge-info'
    elif op_type.startswith('scrap_'):
        return 'badge-danger'
    elif op_type.startswith('user_'):
        return 'badge-warning'
    return 'badge-secondary'


@logs_bp.route('/logs')
@login_required
def list():
    if not current_user.is_admin():
        abort(403)

    operation_type = request.args.get('operation_type', '').strip()
    operator_id = request.args.get('operator_id', type=int)
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()

    query = OperationLog.query

    if operation_type:
        query = query.filter_by(operation_type=operation_type)
    if operator_id:
        query = query.filter_by(operator_id=operator_id)
    if start_date:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        query = query.filter(OperationLog.created_at >= start_dt)
    if end_date:
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        end_dt = end_dt.replace(hour=23, minute=59, second=59)
        query = query.filter(OperationLog.created_at <= end_dt)

    logs = query.order_by(OperationLog.id.desc()).all()
    operators = User.query.order_by(User.real_name).all()
    operation_types = Config.OPERATION_TYPES

    return render_template('logs/list.html',
                           logs=logs,
                           operators=operators,
                           operation_types=operation_types,
                           operation_type=operation_type,
                           operator_id=operator_id,
                           start_date=start_date,
                           end_date=end_date,
                           get_operation_type_text=get_operation_type_text,
                           get_badge_class=get_badge_class)
