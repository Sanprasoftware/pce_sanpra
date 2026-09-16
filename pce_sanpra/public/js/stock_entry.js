frappe.ui.form.on('Stock Entry', {
	setup(frm) {
        frm.set_query("custom_cost_center", function() {
            return {
                filters: {
                    is_group: 0
                }
            };
        });
    }
})