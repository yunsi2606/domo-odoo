# POS Tailoring & Alteration Tracker (`pos_tailoring`)

## 1. Objective
Adds internal tailoring commands and instructional text flags per order line directly inside the POS (Point of Sale) GUI bridging cashier communication with the tailoring/workshop department.

## 2. Business Workflow
- **Order Input**: Using Owl Javascript components on the Point of Sale, Cashiers are greeted with a new "May đo / Sửa" button embedded in the order action frame.
- **Instruction Setting**: 
  - Selecting a line-item on the shopping cart activates the button.
  - Toggling it creates a Pop-up requiring detail parameters like sleeve shortening strings, waist tapering size values, or complete custom notes.
- **Partial Cash / Deposits**: 
  - If it's a tailoring task, the user enables 'Deposit' mode natively on the modal screen. They can select exactly 30% (Standard) or any bespoke interval setting for the downpayment.
  - The POS instantly slices the unit price of the item forcing the customer to only pay up exactly the deposit portion required allowing an Odoo back-end Debt/Receivable balance to accumulate structurally.

## 3. Important Notes & System Automations
**Prerequisites for Users**:
- Admins do not need to configure anything. This is loaded natively into the Owl Point of Sale bundle upon installation.

**What the System Does Automatically**:
- **Invoice Re-calculation**: Selecting a deposit percentage mathematically alters the exact `unit_price`, appending a custom explicit `[TAILORING – CỌC %(Deposit)] Note-Instruction` format visually to the order detail so receipts print transparently stating the product was subject to a partial advance.
- **Backend Syncing via JS Override**: Instead of data evaporating upon checkout closure, the code intercepts the native Odoo `_order_line_fields` JSON dictation. Meaning, it forces the `is_tailoring`, `tailoring_note`, and deposit variables seamlessly into the Python backend `pos.order.line` table so the warehouse/accounting app users can review these properties after the customer left.
