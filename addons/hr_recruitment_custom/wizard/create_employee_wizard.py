# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CreateEmployeeWizard(models.TransientModel):
    """
    Wizard chuyển đổi ứng viên trúng tuyển thành nhân viên mới.
    Tự động chuyển toàn bộ thông tin từ hồ sơ ứng viên sang hồ sơ nhân viên.
    """
    _name = 'hr.recruitment.create.employee.wizard'
    _description = 'Create Employee from Applicant'

    # Applicant & Offer
    applicant_id = fields.Many2one(
        'hr.applicant',
        string='Applicant',
        required=True,
        readonly=True,
    )
    offer_letter_id = fields.Many2one(
        'hr.offer.letter',
        string='Offer Letter',
        readonly=True,
    )

    # === Employee Information ===
    employee_name = fields.Char(
        string='Employee Name',
        compute='_compute_from_applicant',
        store=True,
        readonly=False,
    )
    job_id = fields.Many2one(
        'hr.job',
        string='Job Position',
        required=True,
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        required=True,
    )
    work_email = fields.Char(
        string='Work Email',
        help='Email công việc cho nhân viên mới',
    )
    work_phone = fields.Char(
        string='Work Phone',
        help='Số điện thoại công việc',
    )

    # === Contract Details ===
    offered_salary = fields.Float(
        string='Offered Salary',
    )
    start_date = fields.Date(
        string='Start Date',
        required=True,
        default=fields.Date.today,
    )

    # === Company ===
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
    )

    # === Compute ===
    @api.depends('applicant_id')
    def _compute_from_applicant(self):
        for record in self:
            if record.applicant_id:
                record.employee_name = record.applicant_id.partner_name
            else:
                record.employee_name = ''

    # === Action ===
    def action_create_employee(self):
        """Create employee from applicant data"""
        self.ensure_one()
        applicant = self.applicant_id

        if not applicant:
            raise UserError(_('No applicant selected.'))

        # Check if already converted
        if applicant.employee_id:
            raise UserError(_(
                'This applicant has already been converted to employee: %s',
                applicant.employee_id.name,
            ))

        # Create employee
        employee_vals = {
            'name': self.employee_name or applicant.partner_name,
            'job_id': self.job_id.id,
            'department_id': self.department_id.id,
            'company_id': self.company_id.id,
            'work_email': self.work_email or applicant.email_from,
            'work_phone': self.work_phone or applicant.partner_phone,
            'join_date': self.start_date,
            'employee_status': 'probation',
        }

        # Add personal info if available
        if hasattr(applicant, 'date_of_birth') and applicant.date_of_birth:
            employee_vals['birthday'] = applicant.date_of_birth
        if hasattr(applicant, 'gender') and applicant.gender:
            employee_vals['gender'] = applicant.gender
        if hasattr(applicant, 'address') and applicant.address:
            employee_vals['private_street'] = applicant.address

        # Link applicant origin (hr_employee_custom cross-link)
        if hasattr(self.env['hr.employee'], 'applicant_id'):
            employee_vals['applicant_id'] = applicant.id

        employee = self.env['hr.employee'].create(employee_vals)

        # Link employee to applicant
        applicant.write({
            'employee_id': employee.id,
            'screening_status': 'hired',
        })

        # Link employee to offer letter
        if self.offer_letter_id:
            self.offer_letter_id.write({'employee_id': employee.id})

        # Update recruitment request
        if applicant.recruitment_request_id:
            request = applicant.recruitment_request_id
            if request.hired_count >= request.number_of_positions:
                request.action_mark_filled()

        # Create notification
        employee.message_post(
            body=_(
                'Employee created from recruitment process. '
                'Applicant: %s, Position: %s',
                applicant.partner_name,
                self.job_id.name,
            ),
            message_type='notification',
        )

        return {
            'name': _('New Employee'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.employee',
            'view_mode': 'form',
            'res_id': employee.id,
            'target': 'current',
        }
