frappe.ui.form.on("Work Order", {
	refresh(frm) {
		if (frm.is_new() && frm.doc.bom_no) {
			set_cost_center_from_bom(frm);
		}
	},

	bom_no(frm) {
		set_cost_center_from_bom(frm);
	},
});

async function set_cost_center_from_bom(frm) {
	const bomNo = frm.doc.bom_no;
	if (!bomNo) {
		await frm.set_value("custom_cost_center", null);
		return;
	}

	const { message } = await frappe.db.get_value("BOM", bomNo, "custom_cost_center");
	if (frm.doc.bom_no === bomNo) {
		const costCenter = message?.custom_cost_center || null;
		await frm.set_value("custom_cost_center", costCenter);
		if (frm.is_new() && costCenter === "Unit-2 - PCE") {
			await frm.set_value("skip_transfer", 1);
		}
	}
}
