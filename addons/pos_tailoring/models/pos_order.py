from odoo import api, fields, models

class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    tailoring_note = fields.Text(
        'Tailoring / Alteration Note',
        help='Internal note for tailoring or alteration instructions (e.g., size adjustments, sleeve length)'
    )
    is_tailoring = fields.Boolean(
        'Is Tailoring/Alteration Item',
        help='Flag to identify this line requires workshop processing'
    )
    deposit_percent = fields.Float(
        'Deposit %',
        default=0.0,
        help='Percentage paid upfront for tailoring orders (e.g. 30 means 30% deposit)'
    )


class PosOrder(models.Model):
    _inherit = 'pos.order'

    has_tailoring = fields.Boolean(compute='_compute_has_tailoring', store=True)

    @api.depends('lines.is_tailoring')
    def _compute_has_tailoring(self):
        for order in self:
            order.has_tailoring = any(line.is_tailoring for line in order.lines)

    @api.model
    def _order_line_fields(self, line, session_id=None):
        fields_dict = super()._order_line_fields(line, session_id=session_id)
        # Add custom fields to be accepted from frontend POS payload
        fields_dict[2].update({
            'tailoring_note': line[2].get('tailoring_note', ''),
            'is_tailoring': line[2].get('is_tailoring', False),
            'deposit_percent': line[2].get('deposit_percent', 0.0),
        })
        return fields_dict
