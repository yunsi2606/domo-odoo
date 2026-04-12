# COD Payment Reconciliation (`account_cod_reconcile`)

## 1. Objective
A wizard designed to automate the labor-intensive step of reconciling Cash on Delivery (COD) payouts from carriers against unpaid invoices and stock transfers in Odoo (`stock.picking`).

## 2. Business Workflow
- **Data Intake**: The accountant accesses `Accounting > Receivables > COD Reconciliation` and uploads a raw CSV file provided by GHN or GHTK detailing all tracking numbers and payout amounts.
- **Data Parsing & Scanning**: 
  - Once uploaded, the first step is parsing. Odoo automatically cross-references every row in the spreadsheet looking for the corresponding native Delivery Order (`stock.picking`) holding that tracking ID.
  - Odoo simultaneously locates the original `account.move` (Invoice) attached to the sales order for that delivery.
- **Review**: The UI splits the data highlighting which ones are "Delivered" and have a matching invoice vs ones returning errors.
- **One-Click Reconciliation**: The Accountant authorizes the final reconciliation step.

## 3. Important Notes & System Automations

**Prerequisites for Users**:
- The delivery must actually be tied correctly to a Sales Order AND it must be fully invoiced in native Odoo before this module runs. If the user hasn't created the invoice natively (`Create Invoice` button on SOS), the reconciliation will fail to locate an open receivable to patch.
- Ensure the uploaded document follows standard CSV mappings or Excel headers. Odoo will check for words like `cod`, `tracking_number`, `status`.

**What the System Does Automatically**:
- **Invoice Register Payment**: If the invoice exists, the system automatically instantiates an `account.payment` document specifying an exact COD incoming amount and date, attaches it to the customer, and performs a native journal drop.
- **Receivable Clearing**: The code silently forces a reconciliation link tying that un-marked invoice line to the newly created payment record (marking the invoice visually as `Paid` or `In Payment` seamlessly).
- **Logistics Status Update**: Without asking the warehouse department, the stock picking document will magically turn its `shipping_status` flag to `delivered` during this wizard operation.
