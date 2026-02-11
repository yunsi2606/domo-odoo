# -*- coding: utf-8 -*-
{
    'name': 'Sale Telegram Notification',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Send order notifications to Telegram group/channel',
    'description': """
Automatically send sale order notifications to Telegram when orders are confirmed.
Features:
- Configure Bot Token and Chat ID in Settings
- Send detailed order info with product lines
- Include direct link to order in Odoo
    """,
    'author': 'Your Company',
    'license': 'LGPL-3',
    'depends': ['sale', 'sale_management', 'website_sale', 'stock', 'payment'],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
