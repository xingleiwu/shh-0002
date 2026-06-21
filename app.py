import os
from flask import Flask, render_template
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from config import Config
from models import db, User, Department, Category, Asset
from datetime import date

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录系统'
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf = CSRFProtect(app)

    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.assets import assets_bp
    from routes.borrow import borrow_bp
    from routes.scrap import scrap_bp
    from routes.inventory import inventory_bp
    from routes.department import department_bp
    from routes.user import user_bp
    from routes.logs import logs_bp
    from routes.repair import repair_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(assets_bp)
    app.register_blueprint(borrow_bp)
    app.register_blueprint(scrap_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(department_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(repair_bp)

    from flask_wtf.csrf import generate_csrf

    @app.context_processor
    def inject_global_vars():
        role_texts = {
            'admin': '系统管理员',
            'dept_admin': '部门管理员',
            'maintainer': '维修人员',
            'employee': '普通员工'
        }
        return {
            'current_user': current_user,
            'role_texts': role_texts,
            'csrf_token': generate_csrf
        }

    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500

    with app.app_context():
        db.create_all()
        init_database()

    return app


def init_database():
    if Department.query.count() == 0:
        depts = ['技术部', '市场部', '财务部', '人力资源部', '行政部']
        for name in depts:
            db.session.add(Department(name=name))
        db.session.commit()

    if Category.query.count() == 0:
        cats = [
            ('电子设备', '电脑、手机、打印机等电子类资产'),
            ('办公家具', '办公桌、椅子、文件柜等家具'),
            ('交通工具', '车辆等交通工具'),
            ('办公设备', '空调、投影仪等办公设备'),
            ('其他', '其他类型资产')
        ]
        for name, desc in cats:
            db.session.add(Category(name=name, description=desc))
        db.session.commit()

    if User.query.count() == 0:
        admin_dept = Department.query.filter_by(name='行政部').first()
        tech_dept = Department.query.filter_by(name='技术部').first()
        market_dept = Department.query.filter_by(name='市场部').first()

        admin = User(username='admin', real_name='系统管理员', role='admin', department_id=admin_dept.id)
        admin.set_password('admin123')
        db.session.add(admin)

        zhangsan = User(username='zhangsan', real_name='张三', role='employee', department_id=tech_dept.id)
        zhangsan.set_password('123456')
        db.session.add(zhangsan)

        lisi = User(username='lisi', real_name='李四', role='dept_admin', department_id=market_dept.id)
        lisi.set_password('123456')
        db.session.add(lisi)

        wangwu = User(username='wangwu', real_name='王五', role='maintainer', department_id=admin_dept.id)
        wangwu.set_password('123456')
        db.session.add(wangwu)

        db.session.commit()

    if Asset.query.count() == 0:
        cat_electronic = Category.query.filter_by(name='电子设备').first()
        cat_furniture = Category.query.filter_by(name='办公家具').first()
        cat_vehicle = Category.query.filter_by(name='交通工具').first()
        cat_equipment = Category.query.filter_by(name='办公设备').first()

        tech_dept = Department.query.filter_by(name='技术部').first()
        market_dept = Department.query.filter_by(name='市场部').first()
        finance_dept = Department.query.filter_by(name='财务部').first()
        hr_dept = Department.query.filter_by(name='人力资源部').first()
        admin_dept = Department.query.filter_by(name='行政部').first()

        sample_assets = [
            Asset(name='ThinkPad X1 Carbon 笔记本电脑', category_id=cat_electronic.id,
                  purchase_price=12999.00, purchase_date=date(2024, 1, 15),
                  department_id=tech_dept.id, responsible_person='张三', status='idle'),
            Asset(name='MacBook Pro 14寸', category_id=cat_electronic.id,
                  purchase_price=14999.00, purchase_date=date(2024, 2, 20),
                  department_id=tech_dept.id, responsible_person='李四', status='in_use'),
            Asset(name='Dell 27寸显示器', category_id=cat_electronic.id,
                  purchase_price=1999.00, purchase_date=date(2024, 1, 20),
                  department_id=tech_dept.id, responsible_person='王五', status='idle'),
            Asset(name='HP LaserJet 打印机', category_id=cat_electronic.id,
                  purchase_price=2599.00, purchase_date=date(2024, 3, 1),
                  department_id=admin_dept.id, responsible_person='赵六', status='in_use'),
            Asset(name='L型办公桌', category_id=cat_furniture.id,
                  purchase_price=899.00, purchase_date=date(2024, 1, 10),
                  department_id=tech_dept.id, responsible_person='张三', status='in_use'),
            Asset(name='人体工学椅', category_id=cat_furniture.id,
                  purchase_price=1599.00, purchase_date=date(2024, 1, 10),
                  department_id=tech_dept.id, responsible_person='张三', status='in_use'),
            Asset(name='文件柜', category_id=cat_furniture.id,
                  purchase_price=699.00, purchase_date=date(2024, 2, 15),
                  department_id=finance_dept.id, responsible_person='财务主管', status='in_use'),
            Asset(name='大众帕萨特', category_id=cat_vehicle.id,
                  purchase_price=199000.00, purchase_date=date(2023, 6, 30),
                  department_id=admin_dept.id, responsible_person='行政主管', status='idle'),
            Asset(name='格力中央空调', category_id=cat_equipment.id,
                  purchase_price=12000.00, purchase_date=date(2023, 5, 15),
                  department_id=admin_dept.id, responsible_person='行政主管', status='in_use'),
            Asset(name='EPSON 投影仪', category_id=cat_equipment.id,
                  purchase_price=4999.00, purchase_date=date(2024, 4, 10),
                  department_id=market_dept.id, responsible_person='市场专员', status='maintenance'),
            Asset(name='iPhone 15 Pro', category_id=cat_electronic.id,
                  purchase_price=8999.00, purchase_date=date(2024, 3, 20),
                  department_id=market_dept.id, responsible_person='销售经理', status='in_use'),
            Asset(name='员工办公桌', category_id=cat_furniture.id,
                  purchase_price=599.00, purchase_date=date(2024, 2, 28),
                  department_id=hr_dept.id, responsible_person='HR专员', status='in_use'),
            Asset(name='会议桌', category_id=cat_furniture.id,
                  purchase_price=3999.00, purchase_date=date(2023, 12, 15),
                  department_id=admin_dept.id, responsible_person='行政主管', status='in_use'),
            Asset(name='服务器机柜', category_id=cat_electronic.id,
                  purchase_price=5999.00, purchase_date=date(2023, 8, 1),
                  department_id=tech_dept.id, responsible_person='IT主管', status='in_use'),
            Asset(name='碎纸机', category_id=cat_equipment.id,
                  purchase_price=899.00, purchase_date=date(2024, 1, 5),
                  department_id=finance_dept.id, responsible_person='财务主管', status='idle'),
        ]

        for asset in sample_assets:
            db.session.add(asset)
        db.session.commit()


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5001)
