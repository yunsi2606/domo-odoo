/** @odoo-module **/

import { GanttModel } from "@web/views/gantt/gantt_model";
import { patch } from "@web/core/utils/patch";

/**
 * Custom Gantt Model for Planning module
 * Handles planning-specific data transformations
 */
patch(GanttModel.prototype, {
    /**
     * @override
     */
    setup(params, services) {
        super.setup(params, services);
        // Initialize planning-specific properties
        this.conflictSlots = new Set();
    },

    /**
     * @override
     * Process loaded data to identify conflicts
     */
    async load(searchConfig) {
        const result = await super.load(searchConfig);

        if (this.metaData.resModel === 'planning.slot') {
            this._processConflicts();
        }

        return result;
    },

    /**
     * Identify conflicting slots
     */
    _processConflicts() {
        this.conflictSlots.clear();

        // Group slots by employee
        const slotsByEmployee = {};
        for (const record of Object.values(this.data.records)) {
            const employeeId = record.employee_id?.[0];
            if (employeeId) {
                if (!slotsByEmployee[employeeId]) {
                    slotsByEmployee[employeeId] = [];
                }
                slotsByEmployee[employeeId].push(record);
            }
        }

        // Check for overlaps within each employee's slots
        for (const slots of Object.values(slotsByEmployee)) {
            for (let i = 0; i < slots.length; i++) {
                for (let j = i + 1; j < slots.length; j++) {
                    if (this._slotsOverlap(slots[i], slots[j])) {
                        this.conflictSlots.add(slots[i].id);
                        this.conflictSlots.add(slots[j].id);
                    }
                }
            }
        }
    },

    /**
     * Check if two slots overlap
     */
    _slotsOverlap(slot1, slot2) {
        const start1 = new Date(slot1.start_datetime);
        const end1 = new Date(slot1.end_datetime);
        const start2 = new Date(slot2.start_datetime);
        const end2 = new Date(slot2.end_datetime);

        return start1 < end2 && start2 < end1;
    },

    /**
     * Check if a slot has conflicts
     */
    hasConflict(recordId) {
        return this.conflictSlots.has(recordId);
    },

    /**
     * Get utilization data for employees
     */
    getEmployeeUtilization(employeeId, startDate, endDate) {
        let totalHours = 0;

        for (const record of Object.values(this.data.records)) {
            if (record.employee_id?.[0] === employeeId) {
                const slotStart = new Date(record.start_datetime);
                const slotEnd = new Date(record.end_datetime);

                // Check if slot is within date range
                if (slotStart >= startDate && slotEnd <= endDate) {
                    totalHours += record.allocated_hours || 0;
                }
            }
        }

        return totalHours;
    },
});
