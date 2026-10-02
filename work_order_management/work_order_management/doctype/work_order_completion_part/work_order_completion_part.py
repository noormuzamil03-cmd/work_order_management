# Copyright (c) 2026, ATS and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class WorkOrderCompletionPart(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		action: DF.Literal["Repaired", "Replaced"]
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		part_name: DF.Data
		qty: DF.Float
		remarks: DF.Data | None
	# end: auto-generated types

	_DOCTYPE_NAME = "Work Order Completion Part"
