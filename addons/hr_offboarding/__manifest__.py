# -*- coding: utf-8 -*-
{
    'name': 'HR Offboarding & Asset Recovery',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Manage employee offboarding and asset recovery process',
    'depends': ['hr', 'hr_contract', 'mail'],
    'data': [
        'security/hr_offboarding_security.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/mail_template_data.xml',
        'views/hr_asset_views.xml',
        'views/hr_offboarding_views.xml',
        'views/menus.xml',
        'report/offboarding_report.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
