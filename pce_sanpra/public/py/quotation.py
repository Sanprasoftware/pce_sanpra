import frappe

from erpnext.selling.doctype.quotation.quotation import (
	make_sales_order as erpnext_make_sales_order,
)


@frappe.whitelist()
def make_sales_order(source_name, target_doc=None, args=None):
	"""Map a Quotation to a Sales Order, including its cost center."""
	sales_order = erpnext_make_sales_order(source_name, target_doc, args)
	sales_order.cost_center = frappe.db.get_value(
		"Quotation", source_name, "custom_cost_center"
	)
	return sales_order
