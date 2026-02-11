# -*- coding: utf-8 -*-
from odoo import models
import logging

_logger = logging.getLogger(__name__)


class StockPickingTelegram(models.Model):
    _inherit = 'stock.picking'

    def _action_done(self):
        """Notify via Telegram when delivery is done."""
        res = super()._action_done()
        
        for picking in self:
            if picking.picking_type_code == 'outgoing' and picking.sale_id:
                order = picking.sale_id
                if not order.x_telegram_delivery_sent:
                    _logger.info(f'=== Delivery done for {order.name} ===')
                    try:
                        order._send_telegram('delivery')
                    except Exception as e:
                        _logger.error(f'Telegram delivery failed: {str(e)}')
        
        return res
