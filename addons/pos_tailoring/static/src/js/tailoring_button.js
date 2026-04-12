/** @odoo-module **/
import { Component, useState } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";
import { makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
import { patch } from "@web/core/utils/patch";

// ─── Extend PosOrderline to carry tailoring fields ───────────────────────────
// Register extra fields so they are loaded/synced by Odoo 18 reactive model
patch(PosOrderline, {
    extraFields: {
        ...(PosOrderline.extraFields || {}),
        tailoring_note: {
            model: "pos.order.line",
            name: "tailoring_note",
            type: "char",
            local: true,
        },
        is_tailoring: {
            model: "pos.order.line",
            name: "is_tailoring",
            type: "boolean",
            local: true,
        },
        deposit_percent: {
            model: "pos.order.line",
            name: "deposit_percent",
            type: "float",
            local: true,
        },
    },
});

patch(PosOrderline.prototype, {
    setup(vals) {
        super.setup(...arguments);
        this.tailoring_note = this.tailoring_note || "";
        this.is_tailoring = this.is_tailoring || false;
        this.deposit_percent = this.deposit_percent || 0;
    },
    serialize(options = {}) {
        const json = super.serialize(...arguments);
        json.tailoring_note = this.tailoring_note;
        json.is_tailoring = this.is_tailoring;
        json.deposit_percent = this.deposit_percent;
        return json;
    },
});

// ─── Tailoring Popup ──────────────────────────────────────────────────────────
export class TailoringPopup extends Component {
    static template = "pos_tailoring.TailoringPopup";
    static components = { Dialog };
    static props = {
        title: { type: String, optional: true },
        confirmText: { type: String, optional: true },
        cancelText: { type: String, optional: true },
        tailoringNote: { type: String, optional: true },
        isTailoring: { type: Boolean, optional: true },
        depositPercent: { type: Number, optional: true },
        getPayload: { type: Function, optional: true },
        close: Function,
    };
    static defaultProps = {
        confirmText: _t("Xác nhận"),
        cancelText: _t("Hủy"),
        title: _t("Ghi chú May đo / Sửa đồ"),
        tailoringNote: "",
        isTailoring: false,
        depositPercent: 30,
    };

    setup() {
        this.state = useState({
            tailoringNote: this.props.tailoringNote,
            isTailoring: this.props.isTailoring,
            depositPercent: this.props.depositPercent,
        });
    }

    confirm() {
        if (this.props.getPayload) {
            this.props.getPayload({
                tailoringNote: this.state.tailoringNote,
                isTailoring: this.state.isTailoring,
                depositPercent: parseFloat(this.state.depositPercent) || 0,
            });
        }
        this.props.close();
    }

    cancel() {
        this.props.close();
    }
}

// ─── Tailoring Button (shown in ControlButtons) ───────────────────────────────
export class TailoringButton extends Component {
    static template = "pos_tailoring.TailoringButton";
    static components = {};

    setup() {
        this.pos = usePos();
        this.dialog = useService("dialog");
    }

    get currentLine() {
        return this.pos.get_order()?.get_selected_orderline();
    }

    async onClick() {
        const line = this.currentLine;
        if (!line) return;

        const payload = await makeAwaitable(this.dialog, TailoringPopup, {
            tailoringNote: line.tailoring_note || "",
            isTailoring: line.is_tailoring || false,
            depositPercent: line.deposit_percent || 30,
        });

        if (payload) {
            line.tailoring_note = payload.tailoringNote;
            line.is_tailoring = payload.isTailoring;
            line.deposit_percent = payload.depositPercent;

            if (payload.isTailoring && payload.depositPercent > 0) {
                const originalPrice = line.get_unit_price();
                const depositPrice = originalPrice * (payload.depositPercent / 100);
                line.set_unit_price(depositPrice);
                line.set_customer_note(`[CỌC ${payload.depositPercent}%] ${payload.tailoringNote}`);
            } else {
                line.set_customer_note(payload.tailoringNote || "");
            }
        }
    }
}

// ─── Register TailoringButton into ControlButtons ────────────────────────────
ControlButtons.components = {
    ...ControlButtons.components,
    TailoringButton,
};
