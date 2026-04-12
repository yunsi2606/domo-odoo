# POS Sales to Payroll Sync (`pos_sales_sync`)

## 1. Objective
Automatically resolves the "Data Silos" problem where POS cashiers record sales disconnected from HR. This module captures total sales and product count per shift per employee within the Odoo Point of Sale (POS) and directly injects them into the Payroll ecosystem (`hr.sales.record`) for automated performance bonus computation.

## 2. Business Workflow
- **During the Shift**: Cashiers use the standard POS interface to invoice orders. The system implicitly records which `hr.employee` is tied to each order.
- **End of Shift / Closing**: 
  - The cashier clicks "Close Session" and verifies the cash in drawer.
  - Upon closing the session, the system automatically loops through all paid/invoiced orders within that session.
- **Data Aggregation**: Sales are grouped by `(Employee, Date)`.
- **Payroll Injection**: The system either creates a new `hr.sales.record` or updates an existing one for the particular employee.

## 3. Important Notes & System Automations

**Prerequisites for Users**:
- Employees executing the sales must have their `hr.employee` record mapped in the POS settings (Login with Employee).
- Orders must reach `invoiced` state or have an `amount_paid > 0` to be counted in the sync.

**What the System Does Automatically**:
- **Zero-touch Data Flow**: The entire `hr.sales.record` creation happens silently when the POS session is closed. No supervisor approval or manual data entry is needed.
- **Continuous Update Mechanism**: If a session was closed but an administrator re-opens it and adds orders, clicking the "Sync Sales to Payroll" manual action button within the closed POS session will overwrite and recalculate the employee's net sales accurately without duplicating records.
- **Shift Detection**: The system evaluates the session's `start_at` hour. If the hour is `< 14` (2 PM), it maps the record to the `morning` shift, otherwise to `afternoon` / `evening`.
