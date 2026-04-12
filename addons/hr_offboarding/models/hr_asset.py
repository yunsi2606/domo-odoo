# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HrAssetCategory(models.Model):
    _name = 'hr.asset.category'
    _description = 'Asset Category'

    name = fields.Char('Category', required=True)
    asset_ids = fields.One2many('hr.asset', 'category_id', 'Assets')


class HrAsset(models.Model):
    _name = 'hr.asset'
    _description = 'Company Asset'
    _inherit = ['mail.thread']
    _rec_name = 'name'

    name = fields.Char('Asset Name', required=True, tracking=True)
    code = fields.Char('Asset Code', copy=False)
    category_id = fields.Many2one('hr.asset.category', 'Category')
    description = fields.Text('Description')
    value = fields.Monetary('Asset Value', currency_field='currency_id',
                            help='Used for compensation calculation if damaged/lost')
    currency_id = fields.Many2one('res.currency', default=lambda s: s.env.company.currency_id)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)

    state = fields.Selection([
        ('available', 'Available'),
        ('assigned', 'Assigned'),
        ('maintenance', 'In Maintenance'),
        ('retired', 'Retired'),
    ], default='available', tracking=True)

    assigned_employee_id = fields.Many2one('hr.employee', 'Assigned To', tracking=True)
    assignment_date = fields.Date('Assigned Date')
    assignment_ids = fields.One2many('hr.asset.assignment', 'asset_id', 'Assignment History')

    def action_assign(self, employee, date=None):
        self.write({
            'state': 'assigned',
            'assigned_employee_id': employee.id,
            'assignment_date': date or fields.Date.today(),
        })
        self.env['hr.asset.assignment'].create({
            'asset_id': self.id,
            'employee_id': employee.id,
            'date_assign': date or fields.Date.today(),
        })

    def action_return(self):
        self.write({
            'state': 'available',
            'assigned_employee_id': False,
            'assignment_date': False,
        })


class HrAssetAssignment(models.Model):
    """Assignment history log per asset"""
    _name = 'hr.asset.assignment'
    _description = 'Asset Assignment History'
    _order = 'date_assign desc'

    asset_id = fields.Many2one('hr.asset', ondelete='cascade', required=True)
    employee_id = fields.Many2one('hr.employee', required=True)
    date_assign = fields.Date('Assigned Date', required=True)
    date_return = fields.Date('Returned Date')
    return_condition = fields.Selection([
        ('good', 'Good'),
        ('damaged', 'Damaged'),
        ('lost', 'Lost'),
    ], string='Return Condition')
    note = fields.Text('Note')
