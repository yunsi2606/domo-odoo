# -*- coding: utf-8 -*-
{
    'name': 'HR Planning',
    'version': '18.0.1.0.0',
    'category': 'Human Resources/Planning',
    'summary': 'Employee Shift Planning and Scheduling',
    'description': """
HR Planning for Odoo 18 Community
=================================
Complete shift planning and scheduling system for employees.

Features:
---------
* **Planning Slots**: Create and manage work shifts with start/end times
* **Planning Roles**: Define job roles/positions for shift assignments
* **Shift Templates**: Reusable templates for common shifts
* **Drag & Drop Scheduling**: Easy calendar-based scheduling
* **Gantt Chart View**: Visual timeline of all shifts
* **Auto-Planning**: Automatically assign open shifts based on roles
* **Conflict Detection**: Warns when employees have overlapping shifts
* **Employee Self-Service**: Employees can view their schedules
* **Publish & Notify**: Send schedule notifications to employees
* **Recurring Shifts**: Create repeating shift patterns
* **Time Off Integration**: Respects employee time off
* **Progress Tracking**: Track allocated vs. worked hours
* **Copy Previous Week**: Quickly duplicate last week's schedule
* **Analytics & Reports**: Planning analysis and statistics
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'license': 'LGPL-3',
    'depends': [
        'hr',
        'hr_holidays',
        'resource',
        'mail',
        'portal',
    ],
    'data': [
        # Security
        'security/hr_planning_security.xml',
        'security/ir.model.access.csv',
        
        # Data
        'data/planning_role_data.xml',
        'data/planning_template_data.xml',
        'data/mail_template_data.xml',
        'data/ir_cron_data.xml',
        
        # Views
        'views/planning_slot_views.xml',
        'views/planning_role_views.xml',
        'views/planning_template_views.xml',
        'views/hr_employee_views.xml',
        'views/res_config_settings_views.xml',
        'views/planning_analysis_views.xml',
        'views/menu.xml',
        
        # Reports
        'report/planning_report.xml',
        'report/planning_slot_templates.xml',
        
        # Wizards
        'wizard/planning_send_views.xml',
        'wizard/planning_slot_copy_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hr_planning/static/src/css/planning.css',
            'hr_planning/static/src/js/planning_gantt_controller.js',
            'hr_planning/static/src/js/planning_gantt_model.js',
            'hr_planning/static/src/js/planning_gantt_renderer.js',
            'hr_planning/static/src/xml/planning_gantt.xml',
        ],
    },
    'demo': [
        'demo/planning_demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
