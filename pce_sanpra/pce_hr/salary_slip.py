# import frappe
# from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee
# from frappe.utils import flt
# from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip as HRMSSalarySlip


# class CustomSalarySlip(HRMSSalarySlip):

#     def get_working_days_details(
#         self,
#         lwp=None,
#         for_preview=0,
#         lwp_days_corrected=None,
#     ):
#         super().get_working_days_details(
#             lwp=lwp,
#             for_preview=for_preview,
#             lwp_days_corrected=lwp_days_corrected,
#         )

#         if for_preview:
#             return

#         extra_days = self._get_extra_working_days_from_holidays()

#         if extra_days:
#             self.total_working_days = flt(self.total_working_days) + extra_days
#             self.payment_days = flt(self.payment_days) + extra_days

#     def _get_extra_working_days_from_holidays(self):
#         holiday_list = get_holiday_list_for_employee(self.employee)

#         if not holiday_list:
#             return 0

#         holiday_dates = frappe.get_all(
#             "Holiday",
#             filters={
#                 "parent": holiday_list,
#                 "parenttype": "Holiday List",
#                 "holiday_date": ("between", [self.start_date, self.end_date]),
#                 "custom_add_hd_in_pd": 1,
#             },
#             pluck="holiday_date",
#         )

#         return len(set(holiday_dates))



import math
import frappe
from frappe.utils import flt, getdate
from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip as HRMSSalarySlip


class CustomSalarySlip(HRMSSalarySlip):

    def get_working_days_details(
        self,
        lwp=None,
        for_preview=0,
        lwp_days_corrected=None,
    ):
        super().get_working_days_details(
            lwp=lwp,
            for_preview=for_preview,
            lwp_days_corrected=lwp_days_corrected,
        )

        if for_preview:
            return

        # Add extra holidays to working/payment days
        extra_days = self._get_extra_working_days_from_holidays()

        if extra_days:
            self.total_working_days = flt(self.total_working_days) + extra_days
            self.payment_days = flt(self.payment_days) + extra_days

        # Calculate Payment Days Salary
        self.set_payment_days_salary()

    def _get_extra_working_days_from_holidays(self):
        holiday_list = get_holiday_list_for_employee(self.employee)

        if not holiday_list:
            return 0

        holiday_dates = frappe.get_all(
            "Holiday",
            filters={
                "parent": holiday_list,
                "parenttype": "Holiday List",
                "holiday_date": ("between", [self.start_date, self.end_date]),
                "custom_add_hd_in_pd": 1,
            },
            pluck="holiday_date",
        )

        return len(set(holiday_dates))

    def set_payment_days_salary(self):
        """Calculate salary based on payment days."""

        self.custom_payment_days_salary = 0

        if not self.employee:
            return

        salary_structure_assignment = self.get_latest_salary_structure_assignment()

        if not salary_structure_assignment:
            return

        total_working_days = flt(self.total_working_days)
        payment_days = flt(self.payment_days)

        if not total_working_days:
            return

        base = flt(salary_structure_assignment.base)

        amount = (base / total_working_days) * payment_days

        decimal_part = amount - math.floor(amount)

        if decimal_part >= 0.50:
            amount = math.ceil(amount)
        else:
            amount = math.floor(amount)

        self.custom_payment_days_salary = flt(amount, 2)

    def get_latest_salary_structure_assignment(self):
        filters = {
            "employee": self.employee,
            "docstatus": 1,
        }

        reference_date = self.end_date or self.start_date

        if reference_date:
            filters["from_date"] = ["<=", getdate(reference_date)]

        return frappe.db.get_value(
            "Salary Structure Assignment",
            filters,
            ["name", "base"],
            order_by="from_date desc, creation desc",
            as_dict=True,
        )