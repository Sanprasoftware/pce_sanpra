# """Custom Employee Checkin rules for PCE."""

# from frappe.utils import get_datetime


# SECOND_SHIFT = "SECOND SHIFT"


# def mark_second_shift_checkout(doc, method=None):
# 	"""Mark a punch as OUT during the configured SECOND SHIFT checkout window.

# 	HRMS has already resolved ``shift_end`` and ``shift_actual_end`` by the
# 	``validate`` event. The latter includes the Shift Type's
# 	``allow_check_out_after_shift_end_time`` value, so no grace duration is
# 	hard-coded here.
# 	"""
# 	if doc.shift != SECOND_SHIFT or not doc.shift_end or not doc.shift_actual_end:
# 		return

# 	checkin_time = get_datetime(doc.time)
# 	shift_end = get_datetime(doc.shift_end)
# 	checkout_window_end = get_datetime(doc.shift_actual_end)

# 	if shift_end <= checkin_time <= checkout_window_end:
# 		doc.log_type = "OUT"
