import frappe
from frappe.utils import add_days, getdate, nowdate


def create_weekly_shift_assignments():
    """Create next shift assignments for rotational-shift employees."""

    start_date = getdate(nowdate())

    employees = frappe.get_all(
        "Employee",
        filters={
            "custom_is_rotational_shift": 1,
            "status": "Active",
        },
        pluck="name",
    )

    for employee in employees:
        try:
            create_next_shift_assignment(employee, start_date)
        except Exception:
            frappe.log_error(
                title="Weekly Shift Assignment Failed",
                message=frappe.get_traceback(),
            )


def create_next_shift_assignment(employee, start_date):
    latest_assignment = get_latest_shift_assignment(employee)

    if not latest_assignment or not latest_assignment.shift_type:
        return

    start_date = get_next_assignment_start_date(latest_assignment, start_date)
    end_date = add_days(start_date, 6)

    next_shift = frappe.db.get_value(
        "Shift Type",
        latest_assignment.shift_type,
        "custom_next_shift",
    )

    if not next_shift:
        return

    if shift_assignment_exists(employee, start_date):
        return

    shift_assignment = frappe.new_doc("Shift Assignment")
    shift_assignment.employee = employee
    shift_assignment.shift_type = next_shift
    shift_assignment.start_date = start_date
    shift_assignment.end_date = end_date
    shift_assignment.insert(ignore_permissions=True)
    shift_assignment.submit()


def get_next_assignment_start_date(latest_assignment, fallback_date):
    if latest_assignment.end_date:
        return add_days(latest_assignment.end_date, 1)

    return fallback_date


def get_latest_shift_assignment(employee):
    return frappe.db.get_value(
        "Shift Assignment",
        filters={
            "employee": employee,
            "docstatus": 1,
        },
        fieldname=["name", "shift_type", "start_date", "end_date"],
        order_by="start_date desc, creation desc",
        as_dict=True,
    )


def shift_assignment_exists(employee, start_date):
    return frappe.db.exists(
        "Shift Assignment",
        {
            "employee": employee,
            "start_date": start_date,
            "docstatus": ["!=", 2],
        },
    )
