from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from models import BorrowRecord, Asset, db
from forms import BorrowApplyForm, BorrowRejectForm
from utils import log_operation
from datetime import datetime

borrow_bp = Blueprint('borrow', __name__)


def get_badge_class(status):
    classes = {
        'pending': 'badge-warning',
        'rejected': 'badge-danger',
        'approved': 'badge-info',
        'in_use': 'badge-success',
        'returned': 'badge-warning',
        'completed': 'badge-secondary'
    }
    return classes.get(status, 'badge-secondary')


def get_status_text(status):
    texts = {
        'pending': '待审批',
        'rejected': '已驳回',
        'approved': '待领用',
        'in_use': '使用中',
        'returned': '待收讫',
        'completed': '已完成'
    }
    return texts.get(status, status)


def can_approve(record):
    if not current_user.is_dept_admin():
        return False
    if current_user.is_admin():
        return True
    return record.asset.department_id == current_user.department_id


@borrow_bp.route('/borrow')
@login_required
def list():
    status = request.args.get('status', '')
    my_applications = request.args.get('my', type=int, default=0)

    query = BorrowRecord.query

    if status:
        query = query.filter_by(status=status)

    if my_applications or not current_user.is_dept_admin():
        query = query.filter_by(applicant_id=current_user.id)

    records = query.order_by(BorrowRecord.id.desc()).all()

    return render_template('borrow/list.html',
                           records=records,
                           status=status,
                           my_applications=my_applications,
                           get_badge_class=get_badge_class,
                           get_status_text=get_status_text,
                           can_approve=can_approve)


@borrow_bp.route('/borrow/apply', defaults={'asset_id': None}, methods=['GET', 'POST'])
@borrow_bp.route('/borrow/apply/<int:asset_id>', methods=['GET', 'POST'])
@login_required
def apply(asset_id):
    form = BorrowApplyForm()

    if asset_id and request.method == 'GET':
        asset = Asset.query.get(asset_id)
        if asset and asset.status == 'idle':
            form.asset_id.data = asset_id

    if form.validate_on_submit():
        asset = Asset.query.get(form.asset_id.data)
        
        if not asset:
            flash('资产不存在！', 'danger')
            return redirect(url_for('borrow.apply'))
        
        if asset.status != 'idle':
            flash('该资产当前不可领用！', 'danger')
            return redirect(url_for('borrow.apply'))
        
        existing_active = BorrowRecord.query.filter(
            BorrowRecord.asset_id == asset.id,
            BorrowRecord.status.in_(['pending', 'approved', 'in_use'])
        ).count()
        
        if existing_active > 0:
            flash('该资产已有未完成的申领申请，请选择其他资产！', 'danger')
            return redirect(url_for('borrow.apply'))

        record = BorrowRecord(
            applicant_id=current_user.id,
            asset_id=form.asset_id.data,
            remark=form.remark.data,
            status='pending'
        )
        db.session.add(record)
        db.session.commit()
        log_operation(
            operation_type='borrow_apply',
            target_id=record.id,
            target_type='borrow',
            target_name=asset.name,
            content=f'申请领用资产：{asset.name}'
        )
        flash('领用申请已提交，请等待审批！', 'success')
        return redirect(url_for('borrow.list'))

    return render_template('borrow/apply.html', form=form)


@borrow_bp.route('/borrow/<int:id>/approve', methods=['POST'])
@login_required
def approve(id):
    record = BorrowRecord.query.get_or_404(id)

    if not can_approve(record):
        abort(403)

    if record.status != 'pending':
        flash('该申请状态不支持审批操作！', 'warning')
        return redirect(url_for('borrow.list'))

    other_approved = BorrowRecord.query.filter(
        BorrowRecord.asset_id == record.asset_id,
        BorrowRecord.status == 'approved',
        BorrowRecord.id != record.id
    ).count()
    
    if other_approved > 0:
        flash('该资产已有其他申请已被批准，无法重复审批！', 'danger')
        return redirect(url_for('borrow.list'))

    record.status = 'approved'
    record.approver_id = current_user.id
    record.approve_date = datetime.now()
    db.session.commit()
    log_operation(
        operation_type='borrow_approve',
        target_id=record.id,
        target_type='borrow',
        target_name=record.asset.name,
        content=f'审批通过领用申请：{record.asset.name}（申请人：{record.applicant.real_name}）'
    )
    flash('申请已通过，待员工确认领用！', 'success')
    return redirect(url_for('borrow.list'))


@borrow_bp.route('/borrow/<int:id>/reject', methods=['GET', 'POST'])
@login_required
def reject(id):
    record = BorrowRecord.query.get_or_404(id)

    if not can_approve(record):
        abort(403)

    if record.status != 'pending':
        flash('该申请状态不支持驳回操作！', 'warning')
        return redirect(url_for('borrow.list'))

    form = BorrowRejectForm()
    if form.validate_on_submit():
        record.status = 'rejected'
        record.approver_id = current_user.id
        record.approve_date = datetime.now()
        record.reject_reason = form.reject_reason.data
        db.session.commit()
        log_operation(
            operation_type='borrow_reject',
            target_id=record.id,
            target_type='borrow',
            target_name=record.asset.name,
            content=f'驳回领用申请：{record.asset.name}（申请人：{record.applicant.real_name}），原因：{form.reject_reason.data}'
        )
        flash('申请已驳回！', 'info')
        return redirect(url_for('borrow.list'))

    return render_template('borrow/reject.html', form=form, record=record)


@borrow_bp.route('/borrow/<int:id>/receive', methods=['POST'])
@login_required
def receive(id):
    record = BorrowRecord.query.get_or_404(id)

    if record.applicant_id != current_user.id:
        abort(403)

    if record.status != 'approved':
        flash('该申请状态不支持领用操作！', 'warning')
        return redirect(url_for('borrow.list'))

    record.status = 'in_use'
    record.receive_date = datetime.now()
    record.asset.status = 'in_use'
    db.session.commit()
    log_operation(
        operation_type='borrow_receive',
        target_id=record.id,
        target_type='borrow',
        target_name=record.asset.name,
        content=f'确认领用资产：{record.asset.name}'
    )
    flash('已确认领用，请妥善保管资产！', 'success')
    return redirect(url_for('borrow.list'))


@borrow_bp.route('/borrow/<int:id>/return', methods=['POST'])
@login_required
def return_asset(id):
    record = BorrowRecord.query.get_or_404(id)

    if record.applicant_id != current_user.id:
        abort(403)

    if record.status != 'in_use':
        flash('该申请状态不支持归还操作！', 'warning')
        return redirect(url_for('borrow.list'))

    record.status = 'returned'
    record.return_request_date = datetime.now()
    db.session.commit()
    log_operation(
        operation_type='borrow_return',
        target_id=record.id,
        target_type='borrow',
        target_name=record.asset.name,
        content=f'申请归还资产：{record.asset.name}'
    )
    flash('归还申请已提交，请等待管理员确认收讫！', 'info')
    return redirect(url_for('borrow.list'))


@borrow_bp.route('/borrow/<int:id>/confirm-return', methods=['POST'])
@login_required
def confirm_return(id):
    record = BorrowRecord.query.get_or_404(id)

    if not can_approve(record):
        abort(403)

    if record.status != 'returned':
        flash('该申请状态不支持确认归还操作！', 'warning')
        return redirect(url_for('borrow.list'))

    record.status = 'completed'
    record.return_confirm_date = datetime.now()
    record.asset.status = 'idle'
    db.session.commit()
    log_operation(
        operation_type='borrow_confirm_return',
        target_id=record.id,
        target_type='borrow',
        target_name=record.asset.name,
        content=f'确认资产已归还：{record.asset.name}（使用人：{record.applicant.real_name}）'
    )
    flash('资产已收讫，申领记录已完成！', 'success')
    return redirect(url_for('borrow.list'))
