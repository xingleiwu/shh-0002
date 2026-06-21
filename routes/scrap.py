from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models import ScrapRecord, Asset, db
from forms import ScrapForm
from utils import log_operation
from datetime import datetime

scrap_bp = Blueprint('scrap', __name__)


@scrap_bp.route('/scrap')
@login_required
def list():
    records = ScrapRecord.query.order_by(ScrapRecord.id.desc()).all()
    return render_template('scrap/list.html', records=records)


@scrap_bp.route('/scrap/new', methods=['GET', 'POST'])
@login_required
def new():
    if not current_user.is_admin():
        abort(403)

    form = ScrapForm()
    if form.validate_on_submit():
        asset = Asset.query.get(form.asset_id.data)
        if not asset:
            flash('资产不存在！', 'danger')
            return redirect(url_for('scrap.new'))

        if asset.status == 'scrapped':
            flash('该资产已报废！', 'warning')
            return redirect(url_for('scrap.new'))

        active_borrow = asset.borrow_records and any(
            r.status in ['pending', 'approved', 'in_use'] for r in asset.borrow_records
        )
        if active_borrow:
            flash('该资产存在未完成的领用记录，请先处理！', 'danger')
            return redirect(url_for('scrap.new'))

        record = ScrapRecord(
            asset_id=form.asset_id.data,
            operator_id=current_user.id,
            reason=form.reason.data,
            scrap_date=form.scrap_date.data
        )
        asset.status = 'scrapped'

        db.session.add(record)
        db.session.commit()
        log_operation(
            operation_type='scrap_create',
            target_id=record.id,
            target_type='scrap',
            target_name=asset.name,
            content=f'报废登记：{asset.name}，原因：{form.reason.data}'
        )
        flash('资产报废登记成功！', 'success')
        return redirect(url_for('scrap.list'))

    return render_template('scrap/form.html', form=form)
