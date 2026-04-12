# Delivery GHN / GHTK Integration (`delivery_ghn`)

## 1. Objective
Eliminate the manual step of jumping between Odoo and carrier portals (KiotViet/GHTK) to print tracking labels. This plugin adds an internal bridge that connects Odoo’s native `stock.picking` directly to the GHN and GHTK APIs. 

## 2. Business Workflow
- **Assign Provider**: The user assigns the "Shipping Provider" field on the delivery method configured on the Sales Order.
- **Pushing Order**: 
  - Once the products are assigned and wrapped, the warehouse manager clicks the custom "**Push to Carrier**" button directly inside the Odoo delivery order.
- **Tracking URL**:
  - The API grabs the generated `tracking_number` and the carrier's `label_url`. 
  - The manager can click the "**Print Label**" action inside Odoo without maintaining a separate GHTK account.
- **Updating Shipping State**: 
  - The system will sync order logistics statuses automatically (e.g. from `Submitted` to `In Transit` to `Delivered`).

## 3. Important Notes & System Automations

**Prerequisites for Users**:
- Admins must configure the appropriate API Tokens, Shop IDs, and pickup location parameters inside the "Delivery Methods" tab natively in Odoo.
- The carrier will only process shipments if the phone number and addresses meet their strict formatting rules.

**What the System Does Automatically**:
- **Status Change Hooks**: Once the user pushes the order to the shipping company, the label URL is recorded natively and it alters the Odoo state flag to `submitted`. 
- **Automated Sync**: An accountant or warehouse admin tracking delays can hit "Sync Status" on any order, to which Odoo responds by making an API call and decoding the JSON status code to standard visual badges (`Delivered` (Green), `In Transit` (Yellow)).
