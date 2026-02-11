# -*- coding: utf-8 -*-
{
    'name': 'Time Off Dashboard Fix',
    'version': '18.0.1.0.0',
    'category': 'Human Resources/Time Off',
    'summary': 'Fix Dashboard to show all leave calendars properly',
    'description': """
Time Off Dashboard Fix
======================

Fixes the Time Off Dashboard view to properly display leave calendars
without requiring navigation to "Everybody's calendar".

The fix modifies the default domain/context of the Dashboard action
to show relevant leave entries.
    """,
    'author': 'Custom Development',
    'depends': ['hr_holidays'],
    'data': [
        'views/hr_leave_dashboard_views.xml',
    ],
    'auto_install': False,
    'installable': True,
    'license': 'LGPL-3',
}
