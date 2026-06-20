from flask import Blueprint, render_template
from flask_login import login_required
from models import Asset, Department, Category, db
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    total_assets = Asset.query.count()
    in_use_count = Asset.query.filter_by(status='in_use').count()
    idle_count = Asset.query.filter_by(status='idle').count()
    scrapped_count = Asset.query.filter_by(status='scrapped').count()

    total_value = db.session.query(func.sum(Asset.purchase_price)).scalar() or 0
    in_use_value = db.session.query(func.sum(Asset.purchase_price)).filter_by(status='in_use').scalar() or 0
    idle_value = db.session.query(func.sum(Asset.purchase_price)).filter_by(status='idle').scalar() or 0

    dept_stats = db.session.query(
        Department.name,
        func.count(Asset.id).label('count'),
        func.sum(Asset.purchase_price).label('value')
    ).join(Asset, Department.id == Asset.department_id)\
     .filter(Asset.status != 'scrapped')\
     .group_by(Department.id, Department.name)\
     .order_by(func.count(Asset.id).desc()).all()

    dept_names = [s[0] for s in dept_stats]
    dept_counts = [s[1] for s in dept_stats]
    dept_values = [float(s[2] or 0) for s in dept_stats]

    cat_stats = db.session.query(
        Category.name,
        func.count(Asset.id).label('count'),
        func.sum(Asset.purchase_price).label('value')
    ).join(Asset, Category.id == Asset.category_id)\
     .filter(Asset.status != 'scrapped')\
     .group_by(Category.id, Category.name)\
     .order_by(func.count(Asset.id).desc()).all()

    cat_names = [s[0] for s in cat_stats]
    cat_counts = [s[1] for s in cat_stats]
    cat_values = [float(s[2] or 0) for s in cat_stats]

    return render_template('dashboard/index.html',
                           total_assets=total_assets,
                           in_use_count=in_use_count,
                           idle_count=idle_count,
                           scrapped_count=scrapped_count,
                           total_value=float(total_value),
                           in_use_value=float(in_use_value),
                           idle_value=float(idle_value),
                           dept_names=dept_names,
                           dept_counts=dept_counts,
                           dept_values=dept_values,
                           cat_names=cat_names,
                           cat_counts=cat_counts,
                           cat_values=cat_values)
