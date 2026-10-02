import frappe
from frappe import _
from frappe.model.document import Document


class WorkOrderSlip(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        amended_from: DF.Link | None
        asset: DF.Data | None
        assigned_department: DF.Link
        date: DF.Date
        defect_description: DF.SmallText
        machine_name: DF.Data | None
        priority: DF.Literal["Urgent", "Normal", "Emergency"]
        reference_no: DF.Data | None
        requested_by: DF.Link | None
        requesting_department: DF.Link
        shift: DF.Link | None
        time: DF.Time | None
        work_order_completion: DF.Link | None
        work_status: DF.Literal["Not Started", "In Progress", "Pending Approval", "Rework Required", "Completed"]
    # end: auto-generated types

    def on_submit(self):
        self.db_set("work_status", "Not Started")

    def on_cancel(self):
        active = frappe.db.get_value(
            "Work Order Completion", {"work_order_slip": self.name, "docstatus": ["!=", 2]}
        )
        if active:
            frappe.throw(_("Work Order Completion {0} exists for this slip. Please cancel it first.")
                         .format(active))