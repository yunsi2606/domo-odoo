# -*- coding: utf-8 -*-
{
    'name': 'COD Reconciliation Wizard',
    'version': '18.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Import carrier COD payment files (GHN/GHTK) and auto-reconcile with delivery orders/invoices',
    'depends': ['account', 'delivery_ghn'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/cod_reconcile_wizard_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
