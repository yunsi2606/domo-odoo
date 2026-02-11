# -*- coding: utf-8 -*-
from odoo import models, api, fields
import requests
import logging
import html
import re

_logger = logging.getLogger(__name__)


class SaleOrderTelegram(models.Model):
    _inherit = 'sale.order'

    x_telegram_order_sent = fields.Boolean(default=False, copy=False)
    x_telegram_confirm_sent = fields.Boolean(default=False, copy=False)
    x_telegram_delivery_sent = fields.Boolean(default=False, copy=False)

    def action_confirm(self):
        """Notify on confirm."""
        res = super().action_confirm()
        _logger.info(f'=== action_confirm called for: {self.mapped("name")} ===')
        for order in self:
            if not order.x_telegram_confirm_sent:
                order._send_telegram('confirm')
        return res

    def _send_telegram(self, event_type):
        """Send Telegram msg for the given event."""
        self.ensure_one()
        _logger.info(f'=== _send_telegram({event_type}) called for {self.name} ===')
        
        # Already sent?
        sent_field = f'x_telegram_{event_type}_sent'
        if hasattr(self, sent_field) and getattr(self, sent_field):
            _logger.info(f'Telegram {event_type} already sent for {self.name}, skipping')
            return
        
        ICP = self.env['ir.config_parameter'].sudo()
        enabled = ICP.get_param('sale_telegram_notification.enabled', 'False')
        bot_token = ICP.get_param('sale_telegram_notification.bot_token', '')
        chat_id = ICP.get_param('sale_telegram_notification.chat_id', '')
        
        _logger.info(f'Config: enabled={enabled}, token={bool(bot_token)}, chat={chat_id}')
        
        if enabled != 'True' or not bot_token or not chat_id:
            _logger.info(f'Telegram disabled or credentials missing')
            return
        
        try:
            message = self._build_message(event_type)
            success = self._call_telegram_api(bot_token, chat_id, message)
            if success and hasattr(self, sent_field):
                self.sudo().write({sent_field: True})
                _logger.info(f'Marked {sent_field}=True for {self.name}')
        except Exception as e:
            _logger.error(f'Telegram failed for {self.name}: {str(e)}', exc_info=True)

    def _escape_html(self, text):
        if not text:
            return ''
        text = str(text)
        text = re.sub(r'<[^>]+>', '', text)
        text = html.escape(text)
        return text

    def _build_message(self, event_type):
        """Format the message for a given event type."""
        self.ensure_one()
        
        ICP = self.env['ir.config_parameter'].sudo()
        base_url = ICP.get_param('sale_telegram_notification.base_url') or ICP.get_param('web.base.url', '')
        order_url = f"{base_url}/odoo/sales/{self.id}" if base_url else ""
        
        currency = self._escape_html(self.currency_id.symbol or self.currency_id.name)
        customer_name = self._escape_html(self.partner_id.name)
        phone = self._escape_html(self.partner_id.phone or self.partner_id.mobile or 'Chưa có')
        email = self._escape_html(self.partner_id.email or 'Chưa có')
        address = self._escape_html(self._get_partner_address())
        
        # Product list
        lines = []
        for line in self.order_line:
            if line.product_id and not line.is_delivery:
                name = self._escape_html(line.product_id.name)
                qty = int(line.product_uom_qty) if line.product_uom_qty == int(line.product_uom_qty) else line.product_uom_qty
                lines.append(f"  • {name} x{qty} = {line.price_subtotal:,.0f}{currency}")
        products = "\n".join(lines) if lines else "  (Không có)"
        
        # Title/emoji per event
        if event_type == 'order':
            title = "🛒 <b>ĐƠN HÀNG WEBSITE MỚI</b>"
            status = "⏳ Chờ xác nhận"
        elif event_type == 'confirm':
            title = "✅ <b>ĐƠN HÀNG ĐÃ XÁC NHẬN</b>"
            status = "📦 Đang chuẩn bị"
        elif event_type == 'delivery':
            title = "� <b>ĐƠN HÀNG ĐÃ GIAO</b>"
            status = "✅ Hoàn thành"
        else:
            title = "📋 <b>ĐƠN HÀNG</b>"
            status = ""
        
        message = f"""{title}

🔖 <b>Mã đơn:</b> {self.name}
📅 <b>Ngày:</b> {self.date_order.strftime('%d/%m/%Y %H:%M') if self.date_order else 'N/A'}
{f"📊 <b>Trạng thái:</b> {status}" if status else ""}

👤 <b>Khách hàng:</b> {customer_name}
📱 <b>SĐT:</b> {phone}
📧 <b>Email:</b> {email}
🏠 <b>Địa chỉ:</b> {address}

📋 <b>Chi tiết:</b>
{products}

💰 <b>Tạm tính:</b> {self.amount_untaxed:,.0f}{currency}
💵 <b>Thuế:</b> {self.amount_tax:,.0f}{currency}
🧾 <b>TỔNG:</b> {self.amount_total:,.0f}{currency}"""

        if order_url:
            message += f"\n\n🔗 <a href='{order_url}'>Xem đơn hàng</a>"
        
        if self.note:
            message += f"\n\n📝 <b>Ghi chú:</b> {self._escape_html(self.note)}"
        
        return message

    def _get_partner_address(self):
        partner = self.partner_shipping_id or self.partner_id
        parts = [p for p in [partner.street, partner.street2, partner.city,
                             partner.state_id.name if partner.state_id else None,
                             partner.country_id.name if partner.country_id else None] if p]
        return ', '.join(parts) if parts else 'Chưa có'

    def _call_telegram_api(self, bot_token, chat_id, message):
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {"chat_id": chat_id, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True}
        _logger.info(f'Calling Telegram API for {self.name}')
        response = requests.post(url, data=data, timeout=10)
        _logger.info(f'Telegram response: {response.status_code}')
        if not response.ok:
            _logger.error(f'Telegram error: {response.text}')
        return response.ok
