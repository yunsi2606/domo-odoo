# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import sys
import os

# Import API client
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from api.shipping_client import GHNClient, GHTKClient


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    tracking_number = fields.Char('Tracking Number (Mã vận đơn)', copy=False, readonly=True)
    shipping_provider = fields.Selection(related='carrier_id.shipping_provider', store=True)
    cod_amount = fields.Monetary('COD Amount', currency_field='currency_id',
                                 help='Cash on delivery amount collected by the carrier')
    currency_id = fields.Many2one('res.currency', default=lambda s: s.env.company.currency_id)
    shipping_status = fields.Selection([
        ('draft', 'Not Submitted'),
        ('submitted', 'Submitted to Carrier'),
        ('picking', 'Carrier is Picking Up'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('returned', 'Returned'),
        ('cancelled', 'Cancelled'),
    ], default='draft', string='Shipping Status', tracking=True)
    label_url = fields.Char('Label URL', readonly=True)

    def action_push_to_carrier(self):
        """Create shipment on GHN or GHTK and retrieve tracking number."""
        self.ensure_one()
        carrier = self.carrier_id
        if not carrier or not carrier.shipping_provider:
            raise UserError('Please set a Shipping Provider on the Delivery Method first.')

        if carrier.shipping_provider == 'ghn':
            self._push_to_ghn(carrier)
        elif carrier.shipping_provider == 'ghtk':
            self._push_to_ghtk(carrier)
        else:
            raise UserError('Provider not supported for auto-push. Enter tracking number manually.')

    def _push_to_ghn(self, carrier):
        if not carrier.ghn_token or not carrier.ghn_shop_id:
            raise UserError('GHN Token and Shop ID must be configured on the delivery method.')

        partner = self.partner_id
        sale = self.sale_id
        weight = sum(self.move_ids.mapped('product_id.weight')) or 0.5

        payload = {
            'payment_type_id': 2,   # 1=shop pays, 2=consignee pays
            'note': self.note or '',
            'required_note': 'KHONGCHOXEMHANG',
            'to_name': partner.name or '',
            'to_phone': partner.phone or partner.mobile or '',
            'to_address': partner.street or '',
            'to_ward_name': partner.street2 or '',
            'to_district_name': partner.city or '',
            'to_province_name': partner.state_id.name if partner.state_id else '',
            'cod_amount': int(self.cod_amount) if self.cod_amount else 0,
            'weight': int(weight * 1000),  # in grams
            'service_id': carrier.ghn_service_id or 2,
            'items': [
                {
                    'name': move.product_id.name[:50],
                    'quantity': int(move.product_uom_qty),
                    'weight': int((move.product_id.weight or 0.1) * 1000),
                }
                for move in self.move_ids
            ],
        }

        client = GHNClient(carrier.ghn_token, carrier.ghn_shop_id)
        result = client.create_order(payload)

        if result.get('code') == 200:
            data = result['data']
            self.write({
                'tracking_number': data.get('order_code'),
                'label_url': data.get('label', ''),
                'shipping_status': 'submitted',
            })
            self.message_post(
                body=f"✅ GHN shipment created. Tracking: <b>{data.get('order_code')}</b>"
            )
        else:
            raise UserError(f"GHN Error: {result.get('message', 'Unknown error')}")

    def _push_to_ghtk(self, carrier):
        if not carrier.ghtk_token:
            raise UserError('GHTK API Token must be configured on the delivery method.')

        partner = self.partner_id
        weight = sum(self.move_ids.mapped('product_id.weight')) or 0.3

        payload = {
            'order': {
                'id': self.name,
                'pick_name': self.env.company.name,
                'pick_address': carrier.ghtk_pick_address or '',
                'pick_province': carrier.ghtk_pick_province or '',
                'pick_district': carrier.ghtk_pick_district or '',
                'pick_tel': self.env.company.phone or '',
                'name': partner.name or '',
                'address': partner.street or '',
                'province': partner.state_id.name if partner.state_id else '',
                'district': partner.city or '',
                'tel': partner.phone or partner.mobile or '',
                'note': self.note or '',
                'value': int(self.cod_amount or 0),
                'transport': 'road',
                'pick_money': int(self.cod_amount or 0),
                'is_freeship': 0,
            },
            'products': [
                {
                    'name': move.product_id.name[:50],
                    'weight': move.product_id.weight or 0.1,
                    'quantity': int(move.product_uom_qty),
                }
                for move in self.move_ids
            ],
        }

        client = GHTKClient(carrier.ghtk_token)
        result = client.create_order(payload)

        if result.get('success'):
            data = result.get('order', {})
            self.write({
                'tracking_number': data.get('label'),
                'shipping_status': 'submitted',
            })
            self.message_post(
                body=f"✅ GHTK shipment created. Tracking: <b>{data.get('label')}</b>"
            )
        else:
            raise UserError(f"GHTK Error: {result.get('message', 'Unknown error')}")

    def action_sync_shipping_status(self):
        """Pull current status from carrier API."""
        self.ensure_one()
        if not self.tracking_number:
            raise UserError('No tracking number. Please push the order to the carrier first.')

        carrier = self.carrier_id
        status_map_ghn = {
            'ready_to_pick': 'submitted',
            'picking': 'picking',
            'money_collect_picking': 'picking',
            'picked': 'in_transit',
            'storing': 'in_transit',
            'transporting': 'in_transit',
            'sorting': 'in_transit',
            'delivering': 'in_transit',
            'money_collect_delivering': 'in_transit',
            'delivered': 'delivered',
            'delivery_fail': 'returned',
            'waiting_to_return': 'returned',
            'return': 'returned',
            'returned': 'returned',
            'cancel': 'cancelled',
        }

        if carrier.shipping_provider == 'ghn':
            client = GHNClient(carrier.ghn_token, carrier.ghn_shop_id)
            result = client.get_order_info(self.tracking_number)
            if result.get('code') == 200:
                ghn_status = result['data'].get('status', '').lower()
                odoo_status = status_map_ghn.get(ghn_status, 'in_transit')
                self.shipping_status = odoo_status
                self.message_post(body=f"Status updated from GHN: {ghn_status} → {odoo_status}")

        elif carrier.shipping_provider == 'ghtk':
            client = GHTKClient(carrier.ghtk_token)
            result = client.get_order_status(self.tracking_number)
            if result.get('success'):
                ghtk_status = result.get('order', {}).get('status_text', '')
                self.message_post(body=f"GHTK Status: <b>{ghtk_status}</b>")

    def action_cancel_shipment(self):
        """Cancel the shipment on the carrier side."""
        self.ensure_one()
        if not self.tracking_number:
            raise UserError('No tracking number to cancel.')
        carrier = self.carrier_id
        if carrier.shipping_provider == 'ghn':
            client = GHNClient(carrier.ghn_token, carrier.ghn_shop_id)
            client.cancel_order([self.tracking_number])
        elif carrier.shipping_provider == 'ghtk':
            client = GHTKClient(carrier.ghtk_token)
            client.cancel_order(self.tracking_number)
        self.shipping_status = 'cancelled'
        self.message_post(body=f"Shipment {self.tracking_number} cancelled on carrier.")
