import frappe
from frappe.utils import flt


def set_check_list_from_work_order(doc, method=None):
    """Copy Work Order checklist rows assigned to this Job Card operation."""
    doc.set("custom_jc_check_list_items", [])
    if not doc.work_order or not doc.operation:
        return

    work_order = frappe.get_doc("Work Order", doc.work_order)
    item_names = [row.item_name for row in work_order.custom_wo_check_list_items if row.item_name]
    if not item_names:
        return

    enabled_items = frappe.get_all(
        "Check List Item",
        filters={"name": ["in", item_names], "disabled": 0},
        pluck="name",
    )
    if not enabled_items:
        return

    allowed_items = set(
        frappe.get_all(
            "Check List Operations",
            filters={
                "parent": ["in", enabled_items],
                "parenttype": "Check List Item",
                "parentfield": "check_list_operations",
                "operations": doc.operation,
            },
            pluck="parent",
        )
    )

    for row in work_order.custom_wo_check_list_items:
        if row.item_name not in allowed_items:
            continue

        doc.append(
            "custom_jc_check_list_items",
            {
                "item_name": row.item_name,
                "uom": row.uom,
                "qty": row.qty,
                "wo_qty": row.wo_qty,
            },
        )


def validate_job_card_qty(doc, method=None):
    if doc.custom_jc_check_list_items:
        for row in doc.custom_jc_check_list_items:
            if flt(row.job_card_qty) > flt(row.wo_qty):
                frappe.throw(
                    f"Row {row.idx}: Job Card quantity ({row.job_card_qty}) cannot exceed Work Order quantity ({row.wo_qty})."
                )

def mandetory_job_card_qty(doc, method=None):
    if doc.custom_jc_check_list_items:
        for row in doc.custom_jc_check_list_items:
            if flt(row.job_card_qty) <= 0:
                frappe.throw(
                    f"Row {row.idx}: Job Card quantity is mandatory."
                )
