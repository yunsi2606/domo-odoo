# -*- coding: utf-8 -*-
from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    shipping_provider = fields.Selection([
        ('ghn', 'GHN (Giao Hàng Nhanh)'),
        ('ghtk', 'GHTK (Giao Hàng Tiết Kiệm)'),
        ('other', 'Other'),
    ], string='Shipping Provider')

    # GHN-specific
    ghn_token = fields.Char('GHN API Token')
    ghn_shop_id = fields.Char('GHN Shop ID')
    ghn_service_id = fields.Integer('GHN Service ID',
                                    help='2: Express | 3: Standard | 5: Saving')

    # GHTK-specific
    ghtk_token = fields.Char('GHTK API Token')
    ghtk_pick_province = fields.Char('GHTK Pickup Province')
    ghtk_pick_district = fields.Char('GHTK Pickup District')
    ghtk_pick_address = fields.Char('GHTK Pickup Address')
