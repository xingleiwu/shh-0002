from flask import Blueprint, render_template, request, abort
from flask_login import login_required, current_user
from models import Asset
from models import Category

department_bp = Blueprint('department', __name__)


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


@department_bp.route('/department/assets')
@login_required
def assets():
    if not current_user.department_id:
        abort(403, '您不属于任何部门')

    search = request.args.get('search', '').strip()
    category_id = request.args.get('category_id', type=int)
    status = request.args.get('status', '')

    query = Asset.query.filter_by(department_id=current_user.department_id)

    if search:
        query = query.filter(Asset.name.contains(search) |
                             Asset.responsible_person.contains(search))
    if category_id:
        query = query.filter_by(category_id=category_id)
    if status:
        query = query.filter_by(status=status)

    assets = query.order_by(Asset.id.desc()).all()
    categories = Category.query.order_by(Category.name).all()

    total_value = sum(float(a.purchase_price) for a in assets)
    in_use_count = sum(1 for a in assets if a.status == 'in_use')
    idle_count = sum(1 for a in assets if a.status == 'idle')

    return render_template('department/assets.html',
                           assets=assets,
                           categories=categories,
                           search=search,
                           category_id=category_id,
                           status=status,
                           total_value=total_value,
                           in_use_count=in_use_count,
                           idle_count=idle_count,
                           get_badge_class=get_badge_class,
                           get_status_text=get_status_text)
