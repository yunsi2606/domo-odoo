# -*- coding: utf-8 -*-
from odoo import api, fields, models
from collections import defaultdict


class PosSession(models.Model):
    _inherit = 'pos.session'

    sales_synced = fields.Boolean('Sales Synced to Payroll', readonly=True)

    def action_pos_session_closing_control(self, balancing_account=False,
                                           amount_to_balance=0, bank_payment_method_diffs=None):
        """Override session close to auto-sync sales per employee."""
        res = super().action_pos_session_closing_control(
            balancing_account=balancing_account,
            amount_to_balance=amount_to_balance,
            bank_payment_method_diffs=bank_payment_method_diffs,
        )
        self._sync_sales_to_payroll()
        return res

    def _sync_sales_to_payroll(self):
        """
        Aggregate paid POS orders by (employee, date, shift) and create/update
        hr.sales.record entries so that payroll bonus calculation has accurate data.
        """
        SalesRecord = self.env['hr.sales.record']
        for session in self:
            if session.sales_synced:
                continue

            # Only paid orders
            orders = session.order_ids.filtered(lambda o: o.state == 'invoiced' or o.amount_paid > 0)

            # Group by (employee_id, date)
            by_employee = defaultdict(lambda: {'total_sales': 0.0, 'total_products': 0})
            for order in orders:
                # employee_id on pos.order is the cashier
                emp = order.employee_id
                if not emp:
                    continue
                date_key = order.date_order.date() if order.date_order else session.start_at.date()
                key = (emp.id, date_key)
                by_employee[key]['total_sales'] += order.amount_total
                by_employee[key]['total_products'] += sum(
                    int(line.qty) for line in order.lines if line.qty > 0
                )
                by_employee[key]['employee'] = emp
                by_employee[key]['date'] = date_key

            for (emp_id, date), data in by_employee.items():
                # Check if a record already exists for this employee/session/date
                existing = SalesRecord.search([
                    ('employee_id', '=', emp_id),
                    ('date', '=', data['date']),
                    ('pos_session_id', '=', session.id),
                ], limit=1)
                if existing:
                    existing.write({
                        'total_sales': data['total_sales'],
                        'total_products': data['total_products'],
                    })
                else:
                    SalesRecord.create({
                        'employee_id': emp_id,
                        'date': data['date'],
                        'total_sales': data['total_sales'],
                        'total_products': data['total_products'],
                        'shift': self._get_shift_from_session(session),
                        'pos_session_id': session.id,
                        'source': 'pos',
                    })

            session.sales_synced = True

    def _get_shift_from_session(self, session):
        """Determine shift label from session start hour."""
        hour = session.start_at.hour if session.start_at else 8
        if hour < 14:
            return 'morning'
        return 'afternoon'

    def action_manual_sync_sales(self):
        """Allow manual re-sync from session form."""
        self.sales_synced = False
        self._sync_sales_to_payroll()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': 'Sales data synced to payroll records.',
                'type': 'success',
            }
        }
