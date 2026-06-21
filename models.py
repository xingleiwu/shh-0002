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


class InventoryCheck(db.Model):
    __tablename__ = 'inventory_checks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='draft')
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    remark = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    items = db.relationship('InventoryItem', backref='inventory', lazy=True, cascade='all, delete-orphan')
    operator = db.relationship('User', backref='inventory_checks', lazy=True)
    department = db.relationship('Department', backref='inventory_checks', lazy=True)

    def get_statistics(self):
        total = len(self.items)
        normal = sum(1 for i in self.items if i.result == 'normal')
        surplus = sum(1 for i in self.items if i.result == 'surplus')
        loss = sum(1 for i in self.items if i.result == 'loss')
        unchecked = sum(1 for i in self.items if i.result is None)
        return {
            'total': total,
            'normal': normal,
            'surplus': surplus,
            'loss': loss,
            'unchecked': unchecked
        }

    def __repr__(self):
        return f'<InventoryCheck {self.title}>'


class InventoryItem(db.Model):
    __tablename__ = 'inventory_items'

    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory_checks.id'), nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False)
    expected_status = db.Column(db.String(20), nullable=False)
    actual_status = db.Column(db.String(20), nullable=True)
    result = db.Column(db.String(20), nullable=True)
    actual_location = db.Column(db.String(100), nullable=True)
    remark = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    asset = db.relationship('Asset', backref='inventory_items', lazy=True)

    def update_result(self):
        if self.actual_status is None:
            self.result = None
        elif self.expected_status == self.actual_status:
            self.result = 'normal'
        elif self.actual_status == 'exists':
            self.result = 'normal'
        else:
            if self.expected_status in ['idle', 'in_use', 'maintenance'] and self.actual_status == 'missing':
                self.result = 'loss'
            elif self.expected_status == 'scrapped' and self.actual_status == 'exists':
                self.result = 'surplus'
            else:
                self.result = 'normal'

    def __repr__(self):
        return f'<InventoryItem {self.id}>'


class OperationLog(db.Model):
    __tablename__ = 'operation_logs'

    id = db.Column(db.Integer, primary_key=True)
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    operation_type = db.Column(db.String(50), nullable=False)
    target_id = db.Column(db.Integer, nullable=True)
    target_type = db.Column(db.String(50), nullable=True)
    target_name = db.Column(db.String(200), nullable=True)
    content = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    operator = db.relationship('User', backref='operation_logs', lazy=True)

    def __repr__(self):
        return f'<OperationLog {self.id}: {self.operation_type}>'
