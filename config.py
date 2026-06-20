import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'assets.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)

    ASSET_STATUS = {
        'idle': '闲置',
        'in_use': '使用中',
        'maintenance': '维修中',
        'scrapped': '已报废'
    }

    BORROW_STATUS = {
        'pending': '待审批',
        'rejected': '已驳回',
        'approved': '待领用',
        'in_use': '使用中',
        'returned': '已归还'
    }

    USER_ROLES = {
        'admin': '系统管理员',
        'dept_admin': '部门管理员',
        'employee': '普通员工'
    }
