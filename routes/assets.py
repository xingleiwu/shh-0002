from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from models import Asset, BorrowRecord, db
from forms import AssetForm
from datetime import datetime

assets_bp = Blueprint('assets', __name__)


def get_badge_class(status):
    classes = {
        'idle': 'badge-success',
        'in_use': 'badge-info',
        'maintenance': 'badge-warning',
        'scrapped': 'badge-danger'
    }
    return classes.get(status, 'badge-secondary')


def get_status_text(status):
    texts = {
        'idle': '闲置',
        'in_use': '使用中',
        'maintenance': '维修中',
        'scrapped': '已报废'
    }
    return texts.get(status, status)


@assets_bp.route('/assets')
@login_required
def list():
    search = request.args.get('search', '').strip()
    category_id = request.args.get('category_id', type=int)
    department_id = request.args.get('department_id', type=int)
    status = request.args.get('status', '')

    query = Asset.query

    if search:
        query = query.filter(Asset.name.contains(search) |
                             Asset.responsible_person.contains(search))
    if category_id:
        query = query.filter_by(category_id=category_id)
    if department_id:
        query = query.filter_by(department_id=department_id)
    if status:
        query = query.filter_by(status=status)

    assets = query.order_by(Asset.id.desc()).all()

    from models import Category, Department
    categories = Category.query.order_by(Category.name).all()
    departments = Department.query.order_by(Department.name).all()

    return render_template('assets/list.html',
                           assets=assets,
                           categories=categories,
                           departments=departments,
                           search=search,
                           category_id=category_id,
                           department_id=department_id,
                           status=status,
                           get_badge_class=get_badge_class,
                           get_status_text=get_status_text)


@assets_bp.route('/assets/new', methods=['GET', 'POST'])
@login_required
def new():
    if not current_user.is_admin():
        abort(403)

    form = AssetForm()
    if form.validate_on_submit():
        asset = Asset(
            name=form.name.data,
            category_id=form.category_id.data,
            purchase_price=form.purchase_price.data,
            purchase_date=form.purchase_date.data,
            department_id=form.department_id.data,
            responsible_person=form.responsible_person.data,
            status=form.status.data
        )
        db.session.add(asset)
        db.session.commit()
        flash('资产录入成功！', 'success')
        return redirect(url_for('assets.list'))

    return render_template('assets/form.html', form=form, is_edit=False)


@assets_bp.route('/assets/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    if not current_user.is_admin():
        abort(403)

    asset = Asset.query.get_or_404(id)
    form = AssetForm(obj=asset)

    if form.validate_on_submit():
        asset.name = form.name.data
        asset.category_id = form.category_id.data
        asset.purchase_price = form.purchase_price.data
        asset.purchase_date = form.purchase_date.data
        asset.department_id = form.department_id.data
        asset.responsible_person = form.responsible_person.data
        asset.status = form.status.data
        db.session.commit()
        flash('资产信息更新成功！', 'success')
        return redirect(url_for('assets.list'))

    return render_template('assets/form.html', form=form, is_edit=True, asset=asset)


@assets_bp.route('/assets/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    if not current_user.is_admin():
        abort(403)

    asset = Asset.query.get_or_404(id)

    borrow_count = BorrowRecord.query.filter_by(asset_id=id).count()
    if borrow_count > 0:
        flash('该资产存在领用记录，无法删除！', 'danger')
        return redirect(url_for('assets.list'))

    db.session.delete(asset)
    db.session.commit()
    flash('资产删除成功！', 'success')
    return redirect(url_for('assets.list'))


@assets_bp.route('/assets/<int:id>')
@login_required
def detail(id):
    asset = Asset.query.get_or_404(id)
    borrow_records = BorrowRecord.query.filter_by(asset_id=id).order_by(BorrowRecord.id.desc()).all()

    borrow_status_map = {
        'pending': '待审批',
        'rejected': '已驳回',
        'approved': '待领用',
        'in_use': '使用中',
        'returned': '已归还'
    }

    return render_template('assets/detail.html',
                           asset=asset,
                           borrow_records=borrow_records,
                           get_badge_class=get_badge_class,
                           get_status_text=get_status_text,
                           borrow_status_map=borrow_status_map)
