from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from models import RepairOrder, Asset, db
from forms import RepairSubmitForm, RepairAssignForm, RepairFinishForm, RepairVerifyForm
from utils import log_operation
from datetime import datetime

repair_bp = Blueprint('repair', __name__)


def get_badge_class(status):
    classes = {
        'pending': 'badge-warning',
        'assigned': 'badge-info',
        'repairing': 'badge-primary',
        'completed': 'badge-success',
        'verified': 'badge-secondary',
        'rejected': 'badge-danger'
    }
    return classes.get(status, 'badge-secondary')


def get_status_text(status):
    texts = {
        'pending': '待派单',
        'assigned': '已派单',
        'repairing': '维修中',
        'completed': '待验收',
        'verified': '已完成',
        'rejected': '已驳回'
    }
    return texts.get(status, status)


def get_fault_level_text(level):
    texts = {
        'normal': '一般',
        'serious': '严重',
        'urgent': '紧急'
    }
    return texts.get(level, level)


def get_fault_level_badge(level):
    classes = {
        'normal': 'badge-secondary',
        'serious': 'badge-warning',
        'urgent': 'badge-danger'
    }
    return classes.get(level, 'badge-secondary')


def can_view_all():
    return current_user.is_admin()


def is_assignee(order):
    return current_user.id == order.assignee_id


@repair_bp.route('/repair')
@login_required
def list():
    status = request.args.get('status', '')
    my_repair = request.args.get('my', type=int, default=0)

    query = RepairOrder.query

    if status:
        query = query.filter_by(status=status)

    if not current_user.is_admin():
        if current_user.is_maintainer():
            if my_repair:
                query = query.filter_by(assignee_id=current_user.id)
        else:
            query = query.filter_by(reporter_id=current_user.id)

    orders = query.order_by(RepairOrder.id.desc()).all()

    return render_template('repair/list.html',
                           orders=orders,
                           status=status,
                           my_repair=my_repair,
                           get_badge_class=get_badge_class,
                           get_status_text=get_status_text,
                           get_fault_level_text=get_fault_level_text,
                           get_fault_level_badge=get_fault_level_badge)


@repair_bp.route('/repair/submit', defaults={'asset_id': None}, methods=['GET', 'POST'])
@repair_bp.route('/repair/submit/<int:asset_id>', methods=['GET', 'POST'])
@login_required
def submit(asset_id):
    form = RepairSubmitForm()

    if asset_id and request.method == 'GET':
        asset = Asset.query.get(asset_id)
        if asset and asset.status != 'scrapped':
            form.asset_id.data = asset_id

    if form.validate_on_submit():
        asset = Asset.query.get(form.asset_id.data)

        if not asset:
            flash('资产不存在！', 'danger')
            return redirect(url_for('repair.submit'))

        if asset.status == 'scrapped':
            flash('该资产已报废，无法报修！', 'danger')
            return redirect(url_for('repair.submit'))

        active_repair = RepairOrder.query.filter(
            RepairOrder.asset_id == asset.id,
            RepairOrder.status.in_(['pending', 'assigned', 'repairing', 'completed'])
        ).count()

        if active_repair > 0:
            flash('该资产已有未完成的维修单！', 'warning')
            return redirect(url_for('repair.list'))

        order = RepairOrder(
            asset_id=form.asset_id.data,
            reporter_id=current_user.id,
            fault_description=form.fault_description.data,
            fault_level=form.fault_level.data,
            status='pending'
        )
        db.session.add(order)
        db.session.commit()

        asset.status = 'maintenance'
        db.session.commit()

        log_operation(
            operation_type='repair_submit',
            target_id=order.id,
            target_type='repair',
            target_name=asset.name,
            content=f'提交报修：{asset.name}，故障等级：{get_fault_level_text(form.fault_level.data)}'
        )
        flash('报修已提交，请等待管理员派单！', 'success')
        return redirect(url_for('repair.list'))

    return render_template('repair/submit.html', form=form)


@repair_bp.route('/repair/<int:id>')
@login_required
def detail(id):
    order = RepairOrder.query.get_or_404(id)

    if not current_user.is_admin() and order.reporter_id != current_user.id and order.assignee_id != current_user.id:
        abort(403)

    return render_template('repair/detail.html',
                           order=order,
                           get_badge_class=get_badge_class,
                           get_status_text=get_status_text,
                           get_fault_level_text=get_fault_level_text,
                           get_fault_level_badge=get_fault_level_badge)


@repair_bp.route('/repair/<int:id>/assign', methods=['GET', 'POST'])
@login_required
def assign(id):
    order = RepairOrder.query.get_or_404(id)

    if not current_user.is_admin():
        abort(403)

    if order.status != 'pending':
        flash('该报修单状态不支持派单操作！', 'warning')
        return redirect(url_for('repair.detail', id=id))

    form = RepairAssignForm()
    if form.validate_on_submit():
        order.status = 'assigned'
        order.assignee_id = form.assignee_id.data
        order.assign_time = datetime.now()
        db.session.commit()

        log_operation(
            operation_type='repair_assign',
            target_id=order.id,
            target_type='repair',
            target_name=order.asset.name,
            content=f'派单给：{order.assignee.real_name if order.assignee else "未知"}'
        )
        flash('派单成功！', 'success')
        return redirect(url_for('repair.detail', id=id))

    return render_template('repair/assign.html', form=form, order=order)


@repair_bp.route('/repair/<int:id>/start', methods=['POST'])
@login_required
def start_repair(id):
    order = RepairOrder.query.get_or_404(id)

    if not is_assignee(order) and not current_user.is_admin():
        abort(403)

    if order.status != 'assigned':
        flash('该报修单状态不支持开始维修操作！', 'warning')
        return redirect(url_for('repair.detail', id=id))

    order.status = 'repairing'
    db.session.commit()

    log_operation(
        operation_type='repair_start',
        target_id=order.id,
        target_type='repair',
        target_name=order.asset.name,
        content='开始维修'
    )
    flash('已开始维修！', 'info')
    return redirect(url_for('repair.detail', id=id))


@repair_bp.route('/repair/<int:id>/finish', methods=['GET', 'POST'])
@login_required
def finish_repair(id):
    order = RepairOrder.query.get_or_404(id)

    if not is_assignee(order) and not current_user.is_admin():
        abort(403)

    if order.status not in ['assigned', 'repairing']:
        flash('该报修单状态不支持完成维修操作！', 'warning')
        return redirect(url_for('repair.detail', id=id))

    form = RepairFinishForm()
    if form.validate_on_submit():
        order.status = 'completed'
        order.repair_content = form.repair_content.data
        order.repair_cost = form.repair_cost.data
        order.repair_finish_time = datetime.now()
        db.session.commit()

        log_operation(
            operation_type='repair_finish',
            target_id=order.id,
            target_type='repair',
            target_name=order.asset.name,
            content=f'维修完成：{form.repair_content.data[:50]}...'
        )
        flash('维修已完成，待管理员验收！', 'success')
        return redirect(url_for('repair.detail', id=id))

    return render_template('repair/finish.html', form=form, order=order)


@repair_bp.route('/repair/<int:id>/verify', methods=['GET', 'POST'])
@login_required
def verify(id):
    order = RepairOrder.query.get_or_404(id)

    if not current_user.is_admin():
        abort(403)

    if order.status != 'completed':
        flash('该报修单状态不支持验收操作！', 'warning')
        return redirect(url_for('repair.detail', id=id))

    form = RepairVerifyForm()
    if form.validate_on_submit():
        order.status = 'verified'
        order.verify_remark = form.verify_remark.data
        order.verify_time = datetime.now()
        order.asset.status = 'idle'
        db.session.commit()

        log_operation(
            operation_type='repair_verify',
            target_id=order.id,
            target_type='repair',
            target_name=order.asset.name,
            content=f'验收通过：{form.verify_remark.data or "无备注"}'
        )
        flash('验收通过，维修完成！', 'success')
        return redirect(url_for('repair.detail', id=id))

    return render_template('repair/verify.html', form=form, order=order)
