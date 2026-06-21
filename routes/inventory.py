from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from models import InventoryCheck, InventoryItem, Asset, db, Department
from forms import InventoryForm, InventoryItemForm
from utils import log_operation
from datetime import datetime
from config import Config

inventory_bp = Blueprint('inventory', __name__)


@inventory_bp.route('/inventory')
@login_required
def list():
    if not current_user.is_admin():
        abort(403)
    checks = InventoryCheck.query.order_by(InventoryCheck.id.desc()).all()
    return render_template('inventory/list.html', checks=checks,
                           inventory_status=Config.INVENTORY_STATUS)


@inventory_bp.route('/inventory/new', methods=['GET', 'POST'])
@login_required
def new():
    if not current_user.is_admin():
        abort(403)

    form = InventoryForm()
    if form.validate_on_submit():
        dept_id = form.department_id.data if form.department_id.data != 0 else None

        check = InventoryCheck(
            title=form.title.data,
            status='draft',
            department_id=dept_id,
            start_date=form.start_date.data,
            operator_id=current_user.id,
            remark=form.remark.data
        )
        db.session.add(check)
        db.session.flush()

        query = Asset.query.filter(Asset.status != 'scrapped')
        if dept_id:
            query = query.filter(Asset.department_id == dept_id)
        assets = query.order_by(Asset.id).all()

        for asset in assets:
            item = InventoryItem(
                inventory_id=check.id,
                asset_id=asset.id,
                expected_status=asset.status
            )
            db.session.add(item)

        db.session.commit()
        log_operation(
            operation_type='inventory_create',
            target_id=check.id,
            target_type='inventory',
            target_name=check.title,
            content=f'创建盘点单：{check.title}，共{len(assets)}项资产'
        )
        flash('盘点单创建成功！', 'success')
        return redirect(url_for('inventory.detail', check_id=check.id))

    return render_template('inventory/form.html', form=form)


@inventory_bp.route('/inventory/<int:check_id>')
@login_required
def detail(check_id):
    if not current_user.is_admin():
        abort(403)

    check = InventoryCheck.query.get_or_404(check_id)
    stats = check.get_statistics()
    return render_template('inventory/detail.html', check=check, stats=stats,
                           inventory_status=Config.INVENTORY_STATUS,
                           inventory_result=Config.INVENTORY_RESULT,
                           asset_status=Config.ASSET_STATUS,
                           inventory_actual_status=Config.INVENTORY_ACTUAL_STATUS)


@inventory_bp.route('/inventory/<int:check_id>/start', methods=['POST'])
@login_required
def start(check_id):
    if not current_user.is_admin():
        abort(403)

    check = InventoryCheck.query.get_or_404(check_id)
    if check.status != 'draft':
        flash('只有草稿状态的盘点单才能开始！', 'warning')
        return redirect(url_for('inventory.detail', check_id=check_id))

    check.status = 'ongoing'
    db.session.commit()
    log_operation(
        operation_type='inventory_start',
        target_id=check.id,
        target_type='inventory',
        target_name=check.title,
        content=f'开始盘点：{check.title}'
    )
    flash('盘点已开始！', 'success')
    return redirect(url_for('inventory.detail', check_id=check_id))


@inventory_bp.route('/inventory/<int:check_id>/complete', methods=['POST'])
@login_required
def complete(check_id):
    if not current_user.is_admin():
        abort(403)

    check = InventoryCheck.query.get_or_404(check_id)
    if check.status != 'ongoing':
        flash('只有进行中的盘点单才能完成！', 'warning')
        return redirect(url_for('inventory.detail', check_id=check_id))

    unchecked = sum(1 for i in check.items if i.result is None)
    if unchecked > 0:
        flash(f'还有 {unchecked} 项资产未盘点，请完成全部盘点后再结束！', 'warning')
        return redirect(url_for('inventory.detail', check_id=check_id))

    check.status = 'completed'
    check.end_date = datetime.now().date()
    db.session.commit()
    log_operation(
        operation_type='inventory_complete',
        target_id=check.id,
        target_type='inventory',
        target_name=check.title,
        content=f'完成盘点：{check.title}'
    )
    flash('盘点已完成！', 'success')
    return redirect(url_for('inventory.detail', check_id=check_id))


@inventory_bp.route('/inventory/<int:check_id>/delete', methods=['POST'])
@login_required
def delete(check_id):
    if not current_user.is_admin():
        abort(403)

    check = InventoryCheck.query.get_or_404(check_id)
    if check.status == 'completed':
        flash('已完成的盘点单不能删除！', 'warning')
        return redirect(url_for('inventory.list'))

    title = check.title
    db.session.delete(check)
    db.session.commit()
    log_operation(
        operation_type='inventory_delete',
        target_id=check_id,
        target_type='inventory',
        target_name=title,
        content=f'删除盘点单：{title}'
    )
    flash('盘点单已删除！', 'success')
    return redirect(url_for('inventory.list'))


@inventory_bp.route('/inventory/item/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    if not current_user.is_admin():
        abort(403)

    item = InventoryItem.query.get_or_404(item_id)
    if item.inventory.status == 'completed':
        flash('已完成的盘点不能修改！', 'warning')
        return redirect(url_for('inventory.detail', check_id=item.inventory_id))

    form = InventoryItemForm(obj=item)
    if form.validate_on_submit():
        item.actual_status = form.actual_status.data
        item.actual_location = form.actual_location.data
        item.remark = form.remark.data
        item.update_result()
        db.session.commit()
        flash('盘点结果已保存！', 'success')
        return redirect(url_for('inventory.detail', check_id=item.inventory_id))

    return render_template('inventory/item_form.html', form=form, item=item,
                           inventory_actual_status=Config.INVENTORY_ACTUAL_STATUS,
                           asset_status=Config.ASSET_STATUS)


@inventory_bp.route('/inventory/<int:check_id>/report')
@login_required
def report(check_id):
    if not current_user.is_admin():
        abort(403)

    check = InventoryCheck.query.get_or_404(check_id)
    stats = check.get_statistics()

    surplus_items = [i for i in check.items if i.result == 'surplus']
    loss_items = [i for i in check.items if i.result == 'loss']
    normal_items = [i for i in check.items if i.result == 'normal']

    total_value = sum(i.asset.purchase_price for i in check.items if i.asset)
    surplus_value = sum(i.asset.purchase_price for i in surplus_items if i.asset)
    loss_value = sum(i.asset.purchase_price for i in loss_items if i.asset)
    normal_value = sum(i.asset.purchase_price for i in normal_items if i.asset)

    by_category = {}
    for item in check.items:
        if item.asset and item.asset.category:
            cat_name = item.asset.category.name
            if cat_name not in by_category:
                by_category[cat_name] = {'total': 0, 'normal': 0, 'surplus': 0, 'loss': 0}
            by_category[cat_name]['total'] += 1
            if item.result == 'normal':
                by_category[cat_name]['normal'] += 1
            elif item.result == 'surplus':
                by_category[cat_name]['surplus'] += 1
            elif item.result == 'loss':
                by_category[cat_name]['loss'] += 1

    return render_template('inventory/report.html', check=check, stats=stats,
                           surplus_items=surplus_items, loss_items=loss_items,
                           normal_items=normal_items,
                           total_value=total_value, surplus_value=surplus_value,
                           loss_value=loss_value, normal_value=normal_value,
                           by_category=by_category,
                           inventory_result=Config.INVENTORY_RESULT,
                           asset_status=Config.ASSET_STATUS)
