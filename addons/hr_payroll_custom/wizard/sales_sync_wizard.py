# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SalesSyncWizard(models.TransientModel):
    _name = 'hr.sales.sync.wizard'
    _description = 'Sync Sales Records from Confirmed Sale Orders'

    date_from = fields.Date('From Date', required=True,
                            default=lambda s: fields.Date.today().replace(day=1))
    date_to = fields.Date('To Date', required=True,
                          default=fields.Date.today)
    employee_ids = fields.Many2many(
        'hr.employee', string='Nhân viên',
        help='Để trống = đồng bộ tất cả nhân viên có đơn hàng trong kỳ'
    )
    overwrite = fields.Boolean(
        'Overwrite old data',
        default=True,
        help='Nếu đã có bản ghi cùng nhân viên + ngày thì cập nhật lại, '
             'bỏ chọn để chỉ thêm mới'
    )
    result_msg = fields.Text('Kết quả', readonly=True)

    def action_sync(self):
        """
        Đọc sale.order (state in sale/done) theo khoảng ngày và salesperson,
        rồi tạo/cập nhật hr.sales.record tương ứng.

        Liên kết:  sale.order.user_id (res.users)
                        → res.users.employee_id  (hr.employee) – mối quan hệ
                   HOẶC tìm hr.employee có user_id khớp.
        Nhóm đơn hàng theo (employee, date) – mỗi ngày là 1 record.
        """
        # Đảm bảo module sale đã cài
        if 'sale.order' not in self.env:
            raise UserError(
                'Module "sale" is not installed. Please install it before using this feature.'
            )

        domain = [
            ('state', 'in', ('sale', 'done')),
            ('date_order', '>=', fields.Datetime.to_datetime(self.date_from)),
            ('date_order', '<', fields.Datetime.to_datetime(self.date_to) + __import__('datetime').timedelta(days=1)),
        ]

        SaleOrder = self.env['sale.order'].sudo()
        Employee = self.env['hr.employee'].sudo()
        SalesRecord = self.env['hr.sales.record'].sudo()

        orders = SaleOrder.search(domain)
        if not orders:
            self.result_msg = 'Not found any sale orders in the selected period.'
            return self._reopen()

        # Gom đơn hàng theo (user_id, date)
        from collections import defaultdict
        grouped = defaultdict(lambda: {'total_sales': 0.0, 'total_products': 0})

        for order in orders:
            if not order.user_id:
                continue
            order_date = order.date_order.date()
            key = (order.user_id.id, order_date)
            grouped[key]['total_sales'] += order.amount_total
            # Tổng số dòng sản phẩm trong đơn (hoặc tổng qty)
            grouped[key]['total_products'] += int(
                sum(line.product_uom_qty for line in order.order_line
                    if line.product_id.type in ('product', 'consu'))
            )

        # Tìm mapping user_id → employee
        user_ids = {uid for uid, _ in grouped.keys()}
        employees_by_user = {}
        for emp in Employee.search([('user_id', 'in', list(user_ids))]):
            employees_by_user[emp.user_id.id] = emp

        # Lọc theo danh sách nhân viên nếu có chọn
        allowed_emp_ids = set(self.employee_ids.ids) if self.employee_ids else None

        created = updated = skipped = 0
        for (user_id, order_date), vals in grouped.items():
            emp = employees_by_user.get(user_id)
            if not emp:
                skipped += 1
                continue
            if allowed_emp_ids and emp.id not in allowed_emp_ids:
                continue

            existing = SalesRecord.search([
                ('employee_id', '=', emp.id),
                ('date', '=', order_date),
                ('source', '=', 'pos'),   # dùng tag 'pos' để phân biệt synced từ sale
            ], limit=1)

            record_vals = {
                'employee_id': emp.id,
                'date': order_date,
                'total_sales': vals['total_sales'],
                'total_products': vals['total_products'],
                'source': 'pos',   # tái dụng enum 'pos' = "Auto-sync từ Sale Orders"
                'note': f'Auto-synced from sale.order [{self.date_from} – {self.date_to}]',
            }

            if existing:
                if self.overwrite:
                    existing.write(record_vals)
                    updated += 1
                else:
                    skipped += 1
            else:
                SalesRecord.create(record_vals)
                created += 1

        self.result_msg = (
            f'Sync completed:\n'
            f'  • Created: {created} records\n'
            f'  • Updated: {updated} records\n'
            f'  • Skipped (no employee found / duplicate): {skipped} records\n'
        )
        return self._reopen()

    def _reopen(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
