import frappe
from frappe.utils import flt

from erpnext.manufacturing.doctype.bom.bom import get_bom_items_as_dict
from erpnext.manufacturing.doctype.work_order.work_order import make_work_order


def set_values_from_bom(doc, method=None):
    """Copy BOM cost center and scaled checklist quantities to a Work Order."""
    if not doc.bom_no:
        doc.custom_cost_center = None
        doc.set("custom_wo_check_list_items", [])
        return

    bom = frappe.get_cached_doc("BOM", doc.bom_no)
    doc.custom_cost_center = bom.custom_cost_center
    if doc.custom_cost_center == "Unit-2 - PCE":
        doc.skip_transfer = 1

    doc.set("custom_wo_check_list_items", [])

    quantity_multiplier = flt(doc.qty) / flt(bom.quantity or 1)
    for row in bom.custom_ct_check_list_items:
        doc.append(
            "custom_wo_check_list_items",
            {
                "item_name": row.item_name,
                "uom": row.uom,
                "qty": row.qty,
                "wo_qty": flt(row.qty) * quantity_multiplier,
            },
        )


def create_work_orders_for_sub_assemblies(doc, method=None):
    """Create draft Work Orders for marked direct sub-assemblies."""
    if not doc.bom_no or not doc.qty:
        return

    bom_rows = get_bom_items_as_dict(
        doc.bom_no,
        doc.company,
        qty=doc.qty,
        fetch_exploded=0,
    )
    bom_items = {}
    for row in bom_rows.values():
        item = bom_items.setdefault(
            row.item_code,
            {"required_qty": 0, "source_warehouse": row.source_warehouse},
        )
        item["required_qty"] += flt(row.qty)
        item["source_warehouse"] = item["source_warehouse"] or row.source_warehouse

    marked_items = set(
        frappe.get_all(
            "Item",
            filters={
                "name": ["in", list(bom_items)],
                "custom_create_automatic_work_order_for_sub_assembly": 1,
            },
            pluck="name",
        )
    )

    for item_code in marked_items:
        required_qty = bom_items[item_code]["required_qty"]
        if not required_qty:
            continue

        bom_no = frappe.db.get_value(
            "BOM",
            {
                "item": item_code,
                "is_active": 1,
                "is_default": 1,
                "docstatus": 1,
            },
            "name",
        )
        if not bom_no:
            continue

        work_order = make_work_order(
            bom_no,
            item_code,
            qty=required_qty,
            project=doc.project,
            use_multi_level_bom=0,
        )
        work_order.company = doc.company
        work_order.planned_start_date = doc.planned_start_date
        work_order.wip_warehouse = doc.wip_warehouse
        work_order.fg_warehouse = bom_items[item_code]["source_warehouse"] or doc.source_warehouse
        work_order.get_items_and_operations_from_bom()
        work_order.insert()
