from models import db, OperationLog
from flask_login import current_user


def log_operation(operation_type, target_id=None, target_type=None, target_name=None, content=None):
    if not current_user.is_authenticated:
        return
    log = OperationLog(
        operator_id=current_user.id,
        operation_type=operation_type,
        target_id=target_id,
        target_type=target_type,
        target_name=target_name,
        content=content
    )
    db.session.add(log)
    db.session.commit()
