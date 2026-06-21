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

    INVENTORY_STATUS = {
        'draft': '草稿',
        'ongoing': '进行中',
        'completed': '已完成'
    }

    INVENTORY_RESULT = {
        'normal': '正常',
        'surplus': '盘盈',
        'loss': '盘亏'
    }

    INVENTORY_ACTUAL_STATUS = {
        'exists': '存在',
        'missing': '缺失',
        'damaged': '损坏'
    }

    OPERATION_TYPES = {
        'asset_create': '新增资产',
        'asset_update': '修改资产',
        'asset_delete': '删除资产',
        'borrow_apply': '领用申请',
        'borrow_approve': '审批通过',
        'borrow_reject': '审批驳回',
        'borrow_receive': '资产领用',
        'borrow_return': '归还申请',
        'borrow_confirm_return': '归还确认',
        'scrap_create': '报废登记',
        'inventory_create': '创建盘点',
        'inventory_start': '开始盘点',
        'inventory_complete': '完成盘点',
        'inventory_delete': '删除盘点',
        'user_create': '新增用户',
        'user_update': '修改用户',
        'user_delete': '删除用户'
    }
