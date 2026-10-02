import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, get_datetime, now_datetime, nowdate, nowtime, time_diff_in_hours

# Workflow stage -> status shown on the Work Order Slip
SLIP_STATUS = {
    "Draft": "In Progress",
    "Pending Approval": "Pending Approval",
    "Rework Required": "Rework Required",
    "Approved": "Completed",
}


class WorkOrderCompletion(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF
        from work_order_management.work_order_management.doctype.work_order_completion_part.work_order_completion_part import WorkOrderCompletionPart

        amended_from: DF.Link | None
        approved_by: DF.Link | None
        approved_on: DF.Datetime | None
        approver_remarks: DF.SmallText | None
        asset: DF.Data | None
        assigned_department: DF.Link | None
        complaint_type: DF.Literal["", "New", "Repeated"]
        completed_by: DF.Link | None
        completion_date: DF.Date | None
        completion_time: DF.Time | None
        defect_description: DF.SmallText | None
        details_of_defects: DF.Text
        downtime_hours: DF.Float
        machine_name: DF.Data | None
        parts: DF.Table[WorkOrderCompletionPart]
        priority: DF.Data | None
        received_by: DF.Link | None
        reference_no: DF.Data | None
        remarks: DF.SmallText | None
        requesting_department: DF.Link | None
        shift: DF.Link | None
        slip_date: DF.Date | None
        slip_time: DF.Time | None
        work_order_slip: DF.Link
        work_status: DF.Literal["Pending", "Completed"]
        workflow_state: DF.Link | None
    # end: auto-generated types

    def validate(self):
        slip = frappe.db.get_value(
            "Work Order Slip", self.work_order_slip, ["docstatus", "date", "time"], as_dict=True
        )
        if not slip or slip.docstatus != 1:
            frappe.throw(_("Work Order Slip {0} must be submitted.").format(self.work_order_slip))

        # Only one active Completion per Slip
        other = frappe.db.get_value("Work Order Completion", {
            "work_order_slip": self.work_order_slip,
            "docstatus": ["!=", 2],
            "name": ["!=", self.name],
        })
        if other:
            frappe.throw(_("A Work Order Completion ({0}) already exists for this slip.").format(other))

        if self.workflow_state == "Pending Approval":
            self.validate_ready_for_approval()
            self.suggest_complaint_type()

        if self.workflow_state == "Rework Required" and not self.approver_remarks:
            frappe.throw(_("Please enter Approver Remarks explaining what needs to be reworked."))

        if self.work_status == "Completed":
            self.completion_date = self.completion_date or nowdate()
            self.completion_time = self.completion_time or nowtime()

        self.downtime_hours = self.get_downtime(slip)

    def validate_ready_for_approval(self):
        required = (
            ("details_of_defects", _("Details of Defects Found & Repair Done")),
            ("completion_date", _("Completion Date")),
            ("completion_time", _("Completion Time")),
            ("completed_by", _("Completed By / Incharge")),
        )
        missing = [label for field, label in required if not self.get(field)]
        if missing:
            frappe.throw(_("Please fill {0} before sending for approval.").format(", ".join(missing)))

    def suggest_complaint_type(self):
        """New or Repeated: was the same machine repaired in the last 30 days?"""
        if self.complaint_type or not self.machine_name:
            return
        since = add_days(self.completion_date or nowdate(), -30)
        repeated = frappe.db.exists("Work Order Completion", {
            "machine_name": self.machine_name,
            "docstatus": 1,
            "completion_date": [">=", since],
            "name": ["!=", self.name],
        })
        self.complaint_type = "Repeated" if repeated else "New"

    def before_submit(self):
        if self.work_status != "Completed":
            frappe.throw(_("You can approve only when Work Status is 'Completed'."))
        self.approved_by = frappe.session.user
        self.approved_on = now_datetime()

    def get_downtime(self, slip):
        if not (slip.date and self.completion_date):
            return 0
        start = get_datetime(f"{slip.date} {slip.time or '00:00:00'}")
        end = get_datetime(f"{self.completion_date} {self.completion_time or '00:00:00'}")
        hours = time_diff_in_hours(end, start)
        if hours < 0:
            frappe.throw(_("Completion Date/Time cannot be before the Slip Date/Time."))
        return round(hours, 1)

    def _sync_slip(self, status, completion):
        frappe.db.set_value("Work Order Slip", self.work_order_slip, {
            "work_status": status,
            "work_order_completion": completion,
        })

    def on_update(self):
        self._sync_slip(SLIP_STATUS.get(self.workflow_state, "In Progress"), self.name)

    def on_submit(self):
        self._sync_slip("Completed", self.name)

    def on_cancel(self):
        self._sync_slip("Not Started", None)

    def on_trash(self):
        self._sync_slip("Not Started", None)