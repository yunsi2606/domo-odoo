# -*- coding: utf-8 -*-
{
    'name': 'Delivery GHN / GHTK Integration',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Delivery',
    'summary': 'Create GHN or GHTK shipments from Odoo Delivery Orders and track COD',
    'depends': ['stock', 'sale', 'stock_delivery'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/stock_picking_views.xml',
        'views/delivery_carrier_views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
