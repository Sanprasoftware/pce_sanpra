frappe.ui.form.on('Material Request', {
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