import frappe

from erpnext.stock.doctype.material_request.material_request import (
	make_purchase_order as erpnext_make_purchase_order,
)


@frappe.whitelist()
def make_purchase_order(source_name, target_doc=None, args=None):
	"""Map a Material Request to a Purchase Order, including its cost center."""
	purchase_order = erpnext_make_purchase_order(source_name, target_doc, args)
	purchase_order.cost_center = frappe.db.get_value(
		"Material Request", source_name, "custom_cost_center"
	)
	return purchase_order
