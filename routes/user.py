from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from models import User, db
from forms import UserForm

user_bp = Blueprint('user', __name__)


def get_role_text(role):
    texts = {
        'admin': '系统管理员',
        'dept_admin': '部门管理员',
        'employee': '普通员工'
    }
    return texts.get(role, role)


def get_role_badge_class(role):
    classes = {
        'admin': 'badge-danger',
        'dept_admin': 'badge-warning',
        'employee': 'badge-secondary'
    }
    return classes.get(role, 'badge-secondary')


@user_bp.route('/users')
@login_required
def list():
    if not current_user.is_admin():
        abort(403)

    department_id = request.args.get('department_id', type=int)
    role = request.args.get('role', '')

    query = User.query

    if department_id:
        query = query.filter_by(department_id=department_id)
    if role:
        query = query.filter_by(role=role)

    users = query.order_by(User.id.desc()).all()

    from models import Department
    departments = Department.query.order_by(Department.name).all()

    return render_template('user/list.html',
                           users=users,
                           departments=departments,
                           department_id=department_id,
                           role=role,
                           get_role_text=get_role_text,
                           get_role_badge_class=get_role_badge_class)


@user_bp.route('/users/new', methods=['GET', 'POST'])
@login_required
def new():
    if not current_user.is_admin():
        abort(403)

    form = UserForm()
    if form.validate_on_submit():
        existing = User.query.filter_by(username=form.username.data).first()
        if existing:
            flash('用户名已存在！', 'danger')
            return redirect(url_for('user.new'))

        if not form.password.data:
            flash('请输入密码！', 'danger')
            return redirect(url_for('user.new'))

        dept_id = form.department_id.data if form.department_id.data != 0 else None

        user = User(
            username=form.username.data,
            real_name=form.real_name.data,
            role=form.role.data,
            department_id=dept_id
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()
        flash('用户创建成功！', 'success')
        return redirect(url_for('user.list'))

    return render_template('user/form.html', form=form, is_edit=False)


@user_bp.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    if not current_user.is_admin():
        abort(403)

    user = User.query.get_or_404(id)
    form = UserForm(obj=user)

    if form.validate_on_submit():
        if user.username != form.username.data:
            existing = User.query.filter_by(username=form.username.data).first()
            if existing:
                flash('用户名已存在！', 'danger')
                return redirect(url_for('user.edit', id=id))

        user.username = form.username.data
        user.real_name = form.real_name.data
        user.role = form.role.data
        user.department_id = form.department_id.data if form.department_id.data != 0 else None

        if form.password.data:
            user.set_password(form.password.data)

        db.session.commit()
        flash('用户信息更新成功！', 'success')
        return redirect(url_for('user.list'))

    form.department_id.data = user.department_id or 0
    return render_template('user/form.html', form=form, is_edit=True, user=user)


@user_bp.route('/users/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    if not current_user.is_admin():
        abort(403)

    user = User.query.get_or_404(id)

    if user.id == current_user.id:
        flash('不能删除自己！', 'danger')
        return redirect(url_for('user.list'))

    borrow_count = len(user.borrow_applications) + len(user.borrow_approvals)
    if borrow_count > 0:
        flash('该用户存在相关记录，无法删除！', 'danger')
        return redirect(url_for('user.list'))

    db.session.delete(user)
    db.session.commit()
    flash('用户删除成功！', 'success')
    return redirect(url_for('user.list'))
