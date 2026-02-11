# -*- coding: utf-8 -*-
from odoo import models, api
import logging

_logger = logging.getLogger(__name__)


class PaymentTransactionTelegram(models.Model):
    """Send Telegram when payment goes through."""
    _inherit = 'payment.transaction'

    def _set_pending(self, state_message=None, **extra_allowed_values):
        """Notify on pending payment."""
        res = super()._set_pending(state_message=state_message, **extra_allowed_values)
        self._notify_sale_order_placed()
        return res

    def _set_done(self, state_message=None, **extra_allowed_values):
        """Notify on payment done."""
        res = super()._set_done(state_message=state_message, **extra_allowed_values)
        self._notify_sale_order_placed()
        return res

    def _notify_sale_order_placed(self):
        """Send notification for linked sale orders."""
        for tx in self:
            if tx.sale_order_ids:
                for order in tx.sale_order_ids:
                    if not order.x_telegram_order_sent:
                        _logger.info(f'=== Payment transaction completed for {order.name} ===')
                        order._send_telegram('order')
