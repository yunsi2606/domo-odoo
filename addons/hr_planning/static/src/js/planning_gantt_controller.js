/** @odoo-module **/

import { GanttController } from "@web/views/gantt/gantt_controller";
import { patch } from "@web/core/utils/patch";

/**
 * Custom Gantt Controller for Planning module
 * Adds planning-specific functionality like copy previous week, auto-plan, etc.
 */
patch(GanttController.prototype, {
    /**
     * @override
     */
    setup() {
        super.setup();
        // Add planning-specific setup if needed
    },

    /**
     * Get additional buttons for the planning gantt view
     */
    get actionButtons() {
        const buttons = super.actionButtons || [];

        if (this.props.resModel === 'planning.slot') {
            buttons.push({
                label: this.env._t("Copy Previous"),
                onClick: () => this.onCopyPreviousWeek(),
                class: "btn btn-secondary",
            });
            buttons.push({
                label: this.env._t("Send"),
                onClick: () => this.onSendPlanning(),
                class: "btn btn-primary",
            });
        }

        return buttons;
    },

    /**
     * Copy previous week's planning
     */
    async onCopyPreviousWeek() {
        return this.actionService.doAction({
            type: 'ir.actions.act_window',
            res_model: 'planning.slot.copy',
            views: [[false, 'form']],
            target: 'new',
            context: {
                default_copy_mode: 'week',
            },
        });
    },

    /**
     * Open send planning wizard
     */
    async onSendPlanning() {
        const selectedIds = this.model.selection || [];
        return this.actionService.doAction({
            type: 'ir.actions.act_window',
            res_model: 'planning.send',
            views: [[false, 'form']],
            target: 'new',
            context: {
                default_slot_ids: selectedIds.length ? [[6, 0, selectedIds]] : [],
            },
        });
    },

    /**
     * Handle slot creation from gantt view drag
     */
    async onCellDragEnd(row, column, evt) {
        const result = await super.onCellDragEnd(row, column, evt);

        // Add custom handling for planning slots
        if (this.props.resModel === 'planning.slot' && result) {
            // Could trigger auto-refresh or notification
            this.notification.add(this.env._t("Shift created successfully"), {
                type: 'success',
            });
        }

        return result;
    },
});
