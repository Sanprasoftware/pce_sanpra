frappe.ui.form.on("Job Card", {
	async complete_job_card(frm) {
		const dialog = frm.job_completion_dialog;
		if (!dialog) {
			return;
		}

		const forQuantity = Number(frm.doc.for_quantity) || 0;
		const totalCompletedQty = Number(frm.doc.total_completed_qty) || 0;
		const completedQty = Math.max(forQuantity - totalCompletedQty, 0);

		await dialog.set_value("for_quantity", forQuantity);
		await dialog.set_value("process_loss_qty", 0);
		await dialog.set_value("completed_qty", completedQty);

		dialog.set_df_property("completed_qty", "read_only", 1);
		dialog.set_df_property("process_loss_qty", "read_only", 1);
	},
});
