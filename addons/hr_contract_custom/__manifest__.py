# -*- coding: utf-8 -*-
{
    'name': 'HR Contract Management Custom',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Quản lý Hợp đồng Nhân viên - Phê duyệt theo cấp, Phụ cấp, Cảnh báo hết hạn',
    'description': """
HR Contract Management Custom Module for Odoo 18

Tính năng chính:
* Luồng phê duyệt hợp đồng 3 cấp (Nhân viên xem → Quản lý chi nhánh tạo/gửi → Giám đốc phê duyệt).
* Bảng phụ cấp chi tiết (đi lại, ăn trưa, điện thoại, nhà ở, khác).
* Cảnh báo hợp đồng sắp hết hạn (30/60 ngày).
* Gia hạn và chấm dứt hợp đồng có kiểm soát.
* Xác nhận điện tử từ phía nhân viên.
    """,
    'author': 'FORHER',
    'website': '',
    'depends': [
        'hr',
        'hr_contract',
        'mail',
        'hr_employee_custom',
    ],
    'data': [
        # Security
        'security/hr_contract_custom_security.xml',
        'security/ir.model.access.csv',
        # Data
        'data/sequence_data.xml',
        'data/cron_data.xml',
        # Wizard views
        'wizard/hr_contract_reject_wizard_views.xml',
        # Views
        'views/hr_contract_views.xml',
        'views/hr_contract_allowance_views.xml',
        'views/hr_contract_custom_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hr_contract_custom/static/src/css/contract.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
