# -*- coding: utf-8 -*-
{
    'name': 'POS Tailoring / Alteration Notes',
    'version': '18.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Add internal tailoring/alteration notes per POS order line, visible as service instructions',
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_order_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_tailoring/static/src/js/tailoring_button.js',
            'pos_tailoring/static/src/xml/tailoring_popup.xml',
        ],
    },
    'installable': True,
    'license': 'LGPL-3',
}
