from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Department(db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    users = db.relationship('User', backref='department', lazy=True)
    assets = db.relationship('Asset', backref='department', lazy=True)

    def __repr__(self):
        return f'<Department {self.name}>'


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    real_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='employee')
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    borrow_applications = db.relationship('BorrowRecord', foreign_keys='BorrowRecord.applicant_id',
                                          backref='applicant', lazy=True)
    borrow_approvals = db.relationship('BorrowRecord', foreign_keys='BorrowRecord.approver_id',
                                       backref='approver', lazy=True)
    scrap_records = db.relationship('ScrapRecord', backref='operator', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def is_dept_admin(self):
        return self.role == 'dept_admin' or self.role == 'admin'

    def __repr__(self):
        return f'<User {self.username}>'


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    assets = db.relationship('Asset', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'


class Asset(db.Model):
    __tablename__ = 'assets'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    purchase_price = db.Column(db.Numeric(10, 2), nullable=False)
    purchase_date = db.Column(db.Date, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    responsible_person = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='idle')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    borrow_records = db.relationship('BorrowRecord', backref='asset', lazy=True)
    scrap_records = db.relationship('ScrapRecord', backref='asset', lazy=True)

    def __repr__(self):
        return f'<Asset {self.name}>'


class BorrowRecord(db.Model):
    __tablename__ = 'borrow_records'

    id = db.Column(db.Integer, primary_key=True)
    applicant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    apply_date = db.Column(db.DateTime, default=datetime.now)
    approver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approve_date = db.Column(db.DateTime, nullable=True)
    receive_date = db.Column(db.DateTime, nullable=True)
    return_request_date = db.Column(db.DateTime, nullable=True)
    return_confirm_date = db.Column(db.DateTime, nullable=True)
    reject_reason = db.Column(db.String(255), nullable=True)
    remark = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<BorrowRecord {self.id}>'


class ScrapRecord(db.Model):
    __tablename__ = 'scrap_records'

    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    scrap_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<ScrapRecord {self.id}>'
