/** @odoo-module **/

import { GanttRenderer } from "@web/views/gantt/gantt_renderer";
import { patch } from "@web/core/utils/patch";

/**
 * Custom Gantt Renderer for Planning module
 * Adds visual enhancements for planning slots
 */
patch(GanttRenderer.prototype, {
    /**
     * @override
     * Add custom CSS classes to pills based on planning state
     */
    getPillClass(pill) {
        let classes = super.getPillClass(pill) || '';

        if (this.props.model.metaData.resModel === 'planning.slot') {
            const record = pill.record;

            // State-based classes
            if (record.state === 'draft') {
                classes += ' o_planning_slot_draft';
            } else if (record.state === 'published') {
                classes += ' o_planning_slot_published';
            } else if (record.state === 'done') {
                classes += ' o_planning_slot_done';
            } else if (record.state === 'cancel') {
                classes += ' o_planning_slot_cancel';
            }

            // Conflict indicator
            if (record.has_conflict) {
                classes += ' o_planning_conflict';
            }
        }

        return classes;
    },

    /**
     * @override
     * Custom pill template data
     */
    getPillContext(pill) {
        const context = super.getPillContext(pill) || {};

        if (this.props.model.metaData.resModel === 'planning.slot') {
            const record = pill.record;

            context.hasConflict = record.has_conflict;
            context.allocatedHours = record.allocated_hours;
            context.roleName = record.role_id?.[1] || '';
            context.employeeName = record.employee_id?.[1] || this.env._t('Open Shift');

            // Calculate time display
            if (record.start_datetime) {
                const start = new Date(record.start_datetime);
                context.startTime = start.toLocaleTimeString('en-GB', {
                    hour: '2-digit',
                    minute: '2-digit'
                });
            }
            if (record.end_datetime) {
                const end = new Date(record.end_datetime);
                context.endTime = end.toLocaleTimeString('en-GB', {
                    hour: '2-digit',
                    minute: '2-digit'
                });
            }
        }

        return context;
    },

    /**
     * Get color for utilization display
     */
    getUtilizationColor(percentage) {
        if (percentage < 50) {
            return 'utilization_low';
        } else if (percentage < 80) {
            return 'utilization_normal';
        } else if (percentage <= 100) {
            return 'utilization_high';
        } else {
            return 'utilization_over';
        }
    },

    /**
     * Format hours for display
     */
    formatHours(hours) {
        const wholeHours = Math.floor(hours);
        const minutes = Math.round((hours - wholeHours) * 60);

        if (minutes === 0) {
            return `${wholeHours}h`;
        }
        return `${wholeHours}h${minutes.toString().padStart(2, '0')}`;
    },
});
