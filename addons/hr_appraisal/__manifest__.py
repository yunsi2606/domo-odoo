# -*- coding: utf-8 -*-
{
    'name': 'HR Appraisal',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Employee Performance Appraisal and Evaluation',
    'description': """
HR Appraisal Module for Odoo 18 Community
==========================================

Features:
---------
* Employee Performance Appraisals
* Self-Assessment and Manager Assessment
* Goal Setting and Tracking
* Skills Evaluation
* 360-Degree Feedback
* Appraisal Meetings
* Performance History and Reports
* Automated Reminders

This module provides a complete performance management system
for evaluating employee performance, setting goals, and tracking progress.
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': [
        'hr',
        'mail',
        'calendar',
    ],
    'data': [
        # Security
        'security/hr_appraisal_security.xml',
        'security/ir.model.access.csv',
        # Data
        'data/hr_appraisal_data.xml',
        'data/mail_template_data.xml',
        'data/ir_cron_data.xml',
        # Views
        'views/hr_appraisal_views.xml',
        'views/hr_appraisal_goal_views.xml',
        'views/hr_appraisal_skill_views.xml',
        'views/hr_appraisal_template_views.xml',
        'views/hr_employee_views.xml',
        # 'views/res_config_settings_views.xml',  # TODO: Fix xpath for Odoo 18
        'views/hr_appraisal_menus.xml',
        # Reports
        'report/hr_appraisal_report.xml',
    ],
    'demo': [
        'demo/hr_appraisal_demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hr_appraisal/static/src/css/appraisal.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
