# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HrSalesRecord(models.Model):
    _name = 'hr.sales.record'
    _description = 'Sales Record per Shift'
    _order = 'date desc'

    employee_id = fields.Many2one('hr.employee', required=True, ondelete='cascade')
    date = fields.Date('Date', required=True)
    shift = fields.Selection([
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon'),
        ('evening', 'Evening'),
    ], string='Shift', help='Work shift for this record')
    total_sales = fields.Float('Sales Amount (VNĐ)')
    total_products = fields.Integer('Products Sold')
    source = fields.Selection([
        ('excel', 'Excel Import'),
        ('manual', 'Manual'),
        ('pos', 'POS Auto-sync'),
    ], default='manual')
    pos_session_id = fields.Many2one('pos.session', 'POS Session', ondelete='set null',
                                     help='Auto-populated when synced from a POS session close')
    note = fields.Char('Note')

    # Aliases for backward compatibility
    sales_amount = fields.Float(related='total_sales', store=False)
    products_sold = fields.Integer(related='total_products', store=False)

    is_this_month = fields.Boolean(
        string='Is This Month',
        compute='_compute_is_this_month',
        search='_search_is_this_month'
    )

    def _compute_is_this_month(self):
        today = fields.Date.context_today(self)
        for r in self:
            if r.date:
                r.is_this_month = (r.date.year == today.year and r.date.month == today.month)
            else:
                r.is_this_month = False

    def _search_is_this_month(self, operator, value):
        if operator != '=' or not value:
            return []
        today = fields.Date.context_today(self)
        start_of_month = today.replace(day=1)
        return [('date', '>=', start_of_month)]


    # Hot bonus preview
    hot_bonus_preview = fields.Float('Hot Bonus (Preview)', compute='_compute_preview')
    livestream_bonus_preview = fields.Float('Livestream Bonus (Preview)', compute='_compute_preview')

    @api.depends('sales_amount', 'products_sold')
    def _compute_preview(self):
        for r in self:
            if r.sales_amount >= 10_000_000:
                r.hot_bonus_preview = 200_000
            elif r.sales_amount >= 7_500_000:
                r.hot_bonus_preview = 150_000
            else:
                r.hot_bonus_preview = 0
            r.livestream_bonus_preview = 200_000 if r.products_sold > 50 else 0
