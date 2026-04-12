# -*- coding: utf-8 -*-
import base64
import io
from odoo import api, fields, models, _
from odoo.exceptions import UserError

try:
    import openpyxl
except ImportError:
    openpyxl = None


class SalesImportWizard(models.TransientModel):
    _name = 'hr.sales.import.wizard'
    _description = 'Import Sales Data from Excel'

    file = fields.Binary('Excel File (.xlsx)', required=True)
    filename = fields.Char()
    date_override = fields.Date('Date (override if not in Excel)')
    result_msg = fields.Text('Result', readonly=True)

    # Expected columns: Employee ID (or Name), Sales Amount, Products Sold, Ca, Date
    # Column mapping (0-indexed): A=emp_id_or_name, B=name, C=sales_amount, D=products_sold, E=shift, F=date

    def action_import(self):
        if not openpyxl:
            raise UserError('openpyxl library is required. Install it: pip install openpyxl')
        if not self.file:
            raise UserError('Please upload an Excel file.')

        data = base64.b64decode(self.file)
        wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        ws = wb.active

        created = 0
        errors = []
        Employee = self.env['hr.employee']
        SalesRecord = self.env['hr.sales.record']

        for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            if not row or not row[0]:
                continue
            try:
                emp_ref = str(row[0]).strip()
                sales_amount = float(row[2] or 0)
                products_sold = int(row[3] or 0)
                shift = str(row[4] or '')
                raw_date = row[5]

                # Resolve date
                rec_date = self.date_override
                if raw_date and not rec_date:
                    if hasattr(raw_date, 'date'):
                        rec_date = raw_date.date()
                    else:
                        from datetime import datetime
                        rec_date = datetime.strptime(str(raw_date), '%Y-%m-%d').date()

                if not rec_date:
                    errors.append(f'Row {i}: No date found.')
                    continue

                # Find employee by ID or name
                emp = Employee.search([('name', 'ilike', emp_ref)], limit=1)
                if not emp:
                    emp = Employee.browse(int(emp_ref)) if emp_ref.isdigit() else None
                if not emp:
                    errors.append(f'Row {i}: Employee "{emp_ref}" not found.')
                    continue

                # Skip if already imported for this date+employee+shift
                existing = SalesRecord.search([
                    ('employee_id', '=', emp.id),
                    ('date', '=', rec_date),
                    ('shift', '=', shift),
                    ('source', '=', 'excel'),
                ], limit=1)
                if existing:
                    existing.write({'total_sales': sales_amount, 'total_products': products_sold})
                else:
                    SalesRecord.create({
                        'employee_id': emp.id,
                        'date': rec_date,
                        'shift': shift,
                        'total_sales': sales_amount,
                        'total_products': products_sold,
                        'source': 'excel',
                    })
                    created += 1
            except Exception as e:
                errors.append(f'Row {i}: {e}')

        msg = f'Imported {created} records.'
        if errors:
            msg += '\nErrors:\n' + '\n'.join(errors[:10])
        self.result_msg = msg
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
