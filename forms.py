from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField, TextAreaField, DecimalField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from models import db, Department, Category, User


class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(1, 50)])
    password = PasswordField('密码', validators=[DataRequired()])
    submit = SubmitField('登录')


class AssetForm(FlaskForm):
    name = StringField('资产名称', validators=[DataRequired(), Length(1, 100)])
    category_id = SelectField('资产分类', coerce=int, validators=[DataRequired()])
    purchase_price = DecimalField('购入价格', validators=[DataRequired(), NumberRange(min=0)],
                                  places=2, rounding=None)
    purchase_date = DateField('购入日期', validators=[DataRequired()])
    department_id = SelectField('使用部门', coerce=int, validators=[DataRequired()])
    responsible_person = StringField('责任人', validators=[DataRequired(), Length(1, 50)])
    status = SelectField('当前状态', choices=[
        ('idle', '闲置'),
        ('in_use', '使用中'),
        ('maintenance', '维修中')
    ], validators=[DataRequired()])
    submit = SubmitField('保存')

    def __init__(self, *args, **kwargs):
        super(AssetForm, self).__init__(*args, **kwargs)
        self.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name).all()]
        self.department_id.choices = [(d.id, d.name) for d in Department.query.order_by(Department.name).all()]


class BorrowApplyForm(FlaskForm):
    asset_id = SelectField('申请资产', coerce=int, validators=[DataRequired()])
    remark = TextAreaField('备注说明', validators=[Optional(), Length(max=500)])
    submit = SubmitField('提交申请')

    def __init__(self, *args, **kwargs):
        super(BorrowApplyForm, self).__init__(*args, **kwargs)
        from models import Asset, BorrowRecord
        from sqlalchemy import not_
        
        active_borrow_subq = db.session.query(BorrowRecord.asset_id).filter(
            BorrowRecord.status.in_(['pending', 'approved', 'in_use'])
        ).distinct()
        
        available_assets = Asset.query.filter(
            Asset.status == 'idle',
            not_(Asset.id.in_(active_borrow_subq))
        ).order_by(Asset.name).all()
        
        self.asset_id.choices = [
            (a.id, f'{a.name} ({a.department.name if a.department else "未分配"})')
            for a in available_assets
        ]


class BorrowRejectForm(FlaskForm):
    reject_reason = TextAreaField('驳回原因', validators=[DataRequired(), Length(1, 255)])
    submit = SubmitField('确认驳回')


class ScrapForm(FlaskForm):
    asset_id = SelectField('报废资产', coerce=int, validators=[DataRequired()])
    reason = TextAreaField('报废原因', validators=[DataRequired(), Length(1, 500)])
    scrap_date = DateField('报废日期', validators=[DataRequired()])
    submit = SubmitField('确认报废')

    def __init__(self, *args, **kwargs):
        super(ScrapForm, self).__init__(*args, **kwargs)
        from models import Asset
        self.asset_id.choices = [
            (a.id, f'{a.name} (¥{a.purchase_price:.2f})')
            for a in Asset.query.filter(Asset.status != 'scrapped').order_by(Asset.name).all()
        ]


class UserForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(1, 50)])
    password = PasswordField('密码', validators=[Optional(), Length(6, 50)])
    real_name = StringField('真实姓名', validators=[DataRequired(), Length(1, 50)])
    role = SelectField('角色', choices=[
        ('employee', '普通员工'),
        ('dept_admin', '部门管理员'),
        ('admin', '系统管理员')
    ], validators=[DataRequired()])
    department_id = SelectField('所属部门', coerce=int, validators=[Optional()])
    submit = SubmitField('保存')

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.department_id.choices = [(0, '无')] + [
            (d.id, d.name) for d in Department.query.order_by(Department.name).all()
        ]
