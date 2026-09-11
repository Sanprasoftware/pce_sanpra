app_name = "pce_sanpra"
app_title = "PCE SANPRA"
app_publisher = "Sanpra Software Solution"
app_description = "PCE SANPRA"
app_email = "sanprasoftwraes@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "pce_sanpra",
# 		"logo": "/assets/pce_sanpra/logo.png",
# 		"title": "PCE SANPRA",
# 		"route": "/pce_sanpra",
# 		"has_permission": "pce_sanpra.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/pce_sanpra/css/pce_sanpra.css"
# app_include_js = "/assets/pce_sanpra/js/pce_sanpra.js"

# include js, css files in header of web template
# web_include_css = "/assets/pce_sanpra/css/pce_sanpra.css"
# web_include_js = "/assets/pce_sanpra/js/pce_sanpra.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "pce_sanpra/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"Work Order": "public/js/work_order.js",
	"Job Card": "public/js/job_card.js",
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "pce_sanpra/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "pce_sanpra.utils.jinja_methods",
# 	"filters": "pce_sanpra.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "pce_sanpra.install.before_install"
# after_install = "pce_sanpra.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "pce_sanpra.uninstall.before_uninstall"
# after_uninstall = "pce_sanpra.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "pce_sanpra.utils.before_app_install"
# after_app_install = "pce_sanpra.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "pce_sanpra.utils.before_app_uninstall"
# after_app_uninstall = "pce_sanpra.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "pce_sanpra.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Work Order": {
		"before_validate": "pce_sanpra.public.py.work_order.set_values_from_bom",
		"after_insert": "pce_sanpra.public.py.work_order.create_work_orders_for_sub_assemblies",
	},
	"Job Card": {
		"before_insert": "pce_sanpra.public.py.job_card.set_check_list_from_work_order",
		"validate": "pce_sanpra.public.py.job_card.validate_job_card_qty",
		"before_submit": "pce_sanpra.public.py.job_card.mandetory_job_card_qty",
	},
}



# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"pce_sanpra.tasks.all"
# 	],
# 	"daily": [
# 		"pce_sanpra.tasks.daily"
# 	],
# 	"hourly": [
# 		"pce_sanpra.tasks.hourly"
# 	],
# 	"weekly": [
# 		"pce_sanpra.tasks.weekly"
# 	],
# 	"monthly": [
# 		"pce_sanpra.tasks.monthly"
# 	],
# }


scheduler_events = {
	"cron": {
		"0 2 * * 3": [
			"pce_sanpra.public.py.shift_assignment.create_weekly_shift_assignments"
		],
	},
}

# Testing
# -------

# before_tests = "pce_sanpra.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "pce_sanpra.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#

override_doctype_class = {
	"Salary Slip": "pce_sanpra.pce_hr.salary_slip.CustomSalarySlip",
}

# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "pce_sanpra.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "pce_sanpra.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["pce_sanpra.utils.before_request"]
# after_request = ["pce_sanpra.utils.after_request"]

# Job Events
# ----------
# before_job = ["pce_sanpra.utils.before_job"]
# after_job = ["pce_sanpra.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"pce_sanpra.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []


# Fixtures

fixtures = [
    {
        "dt": "Custom Field",
        "filters": [
            [
                "name",
                "in",
                [
                    "Item-custom_create_automatic_work_order_for_sub_assembly",
                    "BOM-custom_cost_center",
					"BOM-custom_check_list",
					"BOM-custom_ct_check_list_items",
					"Work Order-custom_cost_center",
					"Work Order-custom_wo_check_list_items",
					"Work Order-custom_check_list",
					"Job Card-custom_check_list_items",
					"Job Card-custom_jc_check_list_items",

                ],
            ]
        ],
    },
	{
		"dt": "Property Setter",
		"filters": [
			[
				"name",
				"in",
				[
					"BOM-scrap_section-hidden",
					"BOM-costing-hidden",
					"BOM-more_info_tab-hidden",
					"BOM-website_section-hidden",
					"BOM-allow_alternative_item-hidden",
					"BOM-track_semi_finished_goods-hidden",
					"Work Order-work_order_configuration-hidden",
					"Work Order-more_info-hidden",
					"Work Order-track_semi_finished_goods-hidden",
					"Work Order-additional_transferred_qty-hidden",
					"Work Order-disassembled_qty-hidden",
					"Work Order-use_multi_level_bom-default",
					"Job Card-scheduled_time_tab-hidden",
					"Job Card-timing_detail-hidden",
					"Job Card-scrap_items_section-hidden",
					"Job Card-more_information-hidden",
					"Job Card-is_subcontracted-hidden",
					"Job Card-production_section-hidden",
				],
			]
		],
	},
]
