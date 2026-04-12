# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta


class HrContractAllowance(models.Model):
    """Phụ cấp trong hợp đồng lao động."""

    _name = 'hr.contract.allowance'
    _description = 'Contract Allowance'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)

    contract_id = fields.Many2one(
        'hr.contract',
        string='Contract',
        required=True,
        ondelete='cascade',
    )

    name = fields.Char(
        string='Allowance Name',
        required=True,
    )

    allowance_type = fields.Selection([
        ('transport', 'Transport Allowance'),
        ('meal', 'Meal Allowance'),
        ('phone', 'Phone Allowance'),
        ('housing', 'Housing Allowance'),
        ('responsibility', 'Responsibility Allowance'),
        ('seniority', 'Seniority Allowance'),
        ('other', 'Other'),
    ], string='Allowance Type', required=True, default='other')

    amount = fields.Monetary(
        string='Amount',
        currency_field='currency_id',
        required=True,
    )

    currency_id = fields.Many2one(
        related='contract_id.currency_id',
        store=True,
    )

    notes = fields.Char(string='Notes')
