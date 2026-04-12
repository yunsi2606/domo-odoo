# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import timedelta


class HrEmployeeDocument(models.Model):
    """
    Quản lý giấy tờ và tài liệu của nhân viên.
    Theo dõi hạn hạn, cảnh báo khi sắp hết hạn.
    """
    _name = 'hr.employee.document'
    _description = 'Employee Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'expiry_date asc, name asc'
    _rec_name = 'name'

    # THÔNG TIN CƠ BẢN
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        ondelete='cascade',
        index=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='employee_id.company_id',
        store=True,
    )

    name = fields.Char(
        string='Document Name',
        required=True,
        tracking=True,
    )

    document_type = fields.Selection([
        ('cccd', 'CCCD / CMND'),
        ('driving_license', 'Driving License'),
        ('degree', 'Degree / Certificate'),
        ('insurance', 'Insurance'),
        ('labor_contract', 'Labor Contract'),
        ('tax_code', 'Tax Code'),
        ('passport', 'Passport'),
        ('birth_certificate', 'Birth Certificate'),
        ('marriage_certificate', 'Marriage Certificate'),
        ('residence_book', 'Residence Book'),
        ('other', 'Other'),
    ], string='Document Type', required=True, tracking=True)

    document_number = fields.Char(
        string='Document Number',
        tracking=True,
        help='CCCD number, driving license number, contract number...',
    )

    # NGÀY THÁNG
    issue_date = fields.Date(
        string='Issue Date',
        tracking=True,
    )
    expiry_date = fields.Date(
        string='Expiry Date',
        tracking=True,
    )

    days_to_expiry = fields.Integer(
        string='Days to Expiry',
        compute='_compute_days_to_expiry',
        help='Số ngày còn lại đến ngày hết hạn',
    )

    # FILE ĐÍNH KÈM
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'employee_doc_attachment_rel',
        'document_id',
        'attachment_id',
        string='Attachment',
        help='Upload bản scan / ảnh chụp tài liệu',
    )
    attachment_count = fields.Integer(
        string='Number of files',
        compute='_compute_attachment_count',
    )

    # TRẠNG THÁI
    state = fields.Selection([
        ('draft', 'Draft'),
        ('valid', 'Valid'),
        ('expired', 'Expired'),
        ('lost', 'Lost'),
    ], string='State', default='draft', tracking=True)

    alert_level = fields.Selection([
        ('ok', 'Normal'),
        ('warning', 'Expiring Soon'),
        ('danger', 'Expired'),
    ], string='Alert Level',
       compute='_compute_alert_level',
       store=True,
    )

    notes = fields.Text(string='Notes')

    # COMPUTE METHODS
    @api.depends('expiry_date')
    def _compute_days_to_expiry(self):
        today = fields.Date.today()
        for record in self:
            if record.expiry_date:
                delta = record.expiry_date - today
                record.days_to_expiry = delta.days
            else:
                record.days_to_expiry = 0

    @api.depends('expiry_date', 'state')
    def _compute_alert_level(self):
        today = fields.Date.today()
        warning_threshold = today + timedelta(days=30)
        for record in self:
            if not record.expiry_date or record.state in ('draft', 'lost'):
                record.alert_level = 'ok'
            elif record.expiry_date < today:
                record.alert_level = 'danger'
            elif record.expiry_date <= warning_threshold:
                record.alert_level = 'warning'
            else:
                record.alert_level = 'ok'

    def _compute_attachment_count(self):
        for record in self:
            record.attachment_count = len(record.attachment_ids)

    # ACTION METHODS
    def action_validate(self):
        """Xác minh tài liệu hợp lệ"""
        self.write({'state': 'valid'})

    def action_expire(self):
        """Đánh dấu tài liệu đã hết hạn"""
        self.write({'state': 'expired'})

    def action_lost(self):
        """Đánh dấu tài liệu bị thất lạc"""
        self.write({'state': 'lost'})

    def action_reset_to_draft(self):
        """Đưa về trạng thái chưa xác minh"""
        self.write({'state': 'draft'})

    # CRON: TỰ ĐỘNG CẬP NHẬT TRẠNG THÁI HẾT HẠN
    @api.model
    def _cron_update_expired_documents(self):
        """Tự động đánh dấu tài liệu hết hạn mỗi ngày"""
        expired_docs = self.search([
            ('state', '=', 'valid'),
            ('expiry_date', '<', fields.Date.today()),
        ])
        expired_docs.write({'state': 'expired'})
