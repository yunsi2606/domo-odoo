# -*- coding: utf-8 -*-
{
    'name': 'HR Sales Commission',
    'version': '18.0.1.0.0',
    'category': 'Human Resources/Commission',
    'summary': 'Track sales commissions per employee without payroll',
    'description': """
HR Sales Commission for Odoo 18 Community
==========================================
Commission tracking system without hr_payroll dependency.

Features:
- Commission Rules: Define rates based on order count and revenue
- Commission Records: Monthly aggregation per employee
- Commission Lines: Full traceability to each sale order
- Auto-calculation when stock picking is completed
    """,
    'author': 'Your Company',
    'license': 'LGPL-3',
    'depends': ['sale', 'sale_management', 'stock', 'hr', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/commission_rule_data.xml',
        'views/commission_rule_views.xml',
        'views/commission_record_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
