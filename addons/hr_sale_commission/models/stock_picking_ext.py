# -*- coding: utf-8 -*-
from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


class StockPickingCommission(models.Model):
    """Trigger commission calc when delivery is done."""
    _inherit = 'stock.picking'

    def _action_done(self):
        """Run commission logic after marking as done."""
        result = super()._action_done()
        
        for picking in self:
            try:
                picking._process_commission()
            except Exception as e:
                # Don't block the picking if commission fails
                _logger.error(f'Error processing commission for picking {picking.name}: {str(e)}', exc_info=True)
        
        return result

    def _process_commission(self):
        """Create commission line for this delivery."""
        self.ensure_one()
        
        # Skip non-outgoing or pickings without SO
        if self.picking_type_code != 'outgoing' or not self.sale_id:
            return
        
        sale_order = self.sale_id
        
        # Eligible?
        if not sale_order._is_eligible_for_commission():
            return
        
        # Find employee
        employee = sale_order._get_commission_employee()
        if not employee:
            _logger.warning(f'No employee found for user {sale_order.user_id.name} (order {sale_order.name})')
            return
        
        # Period from delivery date
        delivery_date = self.scheduled_date or fields.Datetime.now()
        month = delivery_date.month
        year = delivery_date.year
        
        # Get/create record for this month
        commission_record = self.env['hr.commission.record'].get_or_create_record(
            employee_id=employee.id,
            month=month,
            year=year,
            company_id=sale_order.company_id.id
        )
        
        if commission_record.state != 'draft':
            _logger.warning(f'Commission record for {employee.name} ({month}/{year}) is {commission_record.state}. Cannot add order.')
            return
        
        # Create line — unique constraint handles duplicates
        try:
            commission_line = self.env['hr.commission.line'].create({
                'commission_record_id': commission_record.id,
                'sale_order_id': sale_order.id,
                'order_amount': sale_order.amount_untaxed,
                'delivery_date': delivery_date,
            })
            sale_order._mark_commission_counted(commission_line)
            _logger.info(f'Commission created for order {sale_order.name} (Employee: {employee.name})')
        except Exception as e:
            if 'unique_sale_order' not in str(e).lower() and 'duplicate' not in str(e).lower():
                raise
            _logger.warning(f'Order {sale_order.name} already has commission line')
