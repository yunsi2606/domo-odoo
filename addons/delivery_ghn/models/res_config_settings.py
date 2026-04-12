# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # These are illustrative — actual creds are per-carrier, not global
    ghn_default_service_id = fields.Integer(
        'Default GHN Service ID',
        config_parameter='delivery_ghn.default_service_id',
        help='2=Express, 3=Standard, 5=Economy'
    )
