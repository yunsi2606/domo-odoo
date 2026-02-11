# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class CommissionLine(models.Model):
    """Each sale order's commission entry."""
    _name = 'hr.commission.line'
    _description = 'Commission Line'
    _order = 'order_date desc, id desc'
    _rec_name = 'sale_order_id'

    commission_record_id = fields.Many2one('hr.commission.record', string='Commission Record',
                                           required=True, ondelete='cascade', index=True)
    sale_order_id = fields.Many2one('sale.order', string='Sale Order', required=True,
                                    ondelete='restrict', index=True)
    order_date = fields.Datetime(string='Order Date', related='sale_order_id.date_order',
                                 store=True, readonly=True)
    order_amount = fields.Float(string='Order Amount', digits='Product Price', required=True)
    delivery_date = fields.Datetime(string='Delivery Date')

    # Display fields
    employee_id = fields.Many2one('hr.employee', related='commission_record_id.employee_id', store=True)
    month = fields.Selection(related='commission_record_id.month', store=True)
    year = fields.Integer(related='commission_record_id.year', store=True)
    state = fields.Selection(related='commission_record_id.state', store=True)
    currency_id = fields.Many2one('res.currency', related='commission_record_id.currency_id', store=True)

    # Prevent duplicate commission per order
    _sql_constraints = [
        ('unique_sale_order', 'UNIQUE(sale_order_id)',
         'This sale order has already been counted for commission!'),
    ]

    @api.constrains('order_amount')
    def _check_order_amount(self):
        for line in self:
            if line.order_amount < 0:
                raise ValidationError('Order amount cannot be negative.')

    @api.model_create_multi
    def create(self, vals_list):
        """Only allow lines for confirmed orders."""
        for vals in vals_list:
            if vals.get('sale_order_id'):
                sale_order = self.env['sale.order'].browse(vals['sale_order_id'])
                if sale_order.state != 'sale':
                    raise ValidationError(f'Sale order {sale_order.name} is not in confirmed state.')
        return super().create(vals_list)

    def unlink(self):
        """Block deletion if record is confirmed/locked."""
        for line in self:
            if line.commission_record_id.state in ('confirmed', 'locked'):
                raise ValidationError('Cannot delete commission lines from confirmed or locked records.')
        return super().unlink()
