# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrContractRejectWizard(models.TransientModel):
    """Wizard nhập lý do từ chối hợp đồng."""

    _name = 'hr.contract.reject.wizard'
    _description = 'Reject Contract'

    contract_id = fields.Many2one(
        'hr.contract',
        string='Contract',
        required=True,
    )
    rejection_reason = fields.Text(
        string='Rejection Reason',
        required=True,
        placeholder='Enter rejection reason...',
    )

    def action_confirm_reject(self):
        """Xác nhận từ chối và ghi log."""
        self.ensure_one()
        contract = self.contract_id
        if contract.approval_state != 'submitted':
            raise UserError(_('The contract is not in the approval pending state.'))
        contract.write({
            'approval_state': 'rejected',
            'rejection_reason': self.rejection_reason,
        })
        contract.message_post(
            body=_('The contract was rejected by %s.\n\nReason: %s') % (
                self.env.user.name,
                self.rejection_reason,
            ),
            subtype_xmlid='mail.mt_note',
        )
        # Thông báo cho người gửi
        if contract.submitted_by and contract.submitted_by.partner_id:
            contract.message_post(
                body=_('The contract of employee <b>%s</b> has been rejected.\nReason: %s') % (
                    contract.employee_id.name,
                    self.rejection_reason,
                ),
                partner_ids=[contract.submitted_by.partner_id.id],
                subtype_xmlid='mail.mt_comment',
            )
        return {'type': 'ir.actions.act_window_close'}
