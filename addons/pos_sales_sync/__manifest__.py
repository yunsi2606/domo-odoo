# -*- coding: utf-8 -*-
{
    'name': 'POS Sales Sync to Payroll',
    'version': '18.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Auto-sync POS session sales per employee to hr.sales.record for payroll bonus calculation',
    'depends': ['point_of_sale', 'hr_payroll_custom'],
    'data': [
        'views/pos_session_views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
