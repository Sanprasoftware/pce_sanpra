frappe.ready(() => {
	const root = document.getElementById("face-checkin-kiosk");
	if (!root) return;

	const style = document.createElement("style");
	style.textContent = `
		.web-form-head > .title, .web-form-footer, .web-form-actions { display: none !important; }
		.web-form-header { padding-bottom: 0 !important; }
		.web-form-introduction { margin-top: 0 !important; }
		.face-kiosk { max-width: 760px; margin: 0 auto; text-align: center; }
		.face-camera { position: relative; overflow: hidden; border-radius: 18px; background: #101828; aspect-ratio: 4 / 3; box-shadow: 0 12px 35px rgba(16,24,40,.18); }
		.face-camera video { width: 100%; height: 100%; object-fit: cover; transform: scaleX(-1); }
		.face-guide { position: absolute; inset: 13% 28%; border: 4px solid rgba(255,255,255,.9); border-radius: 48% 48% 44% 44%; box-shadow: 0 0 0 999px rgba(0,0,0,.18); }
		.face-status { min-height: 82px; margin-top: 18px; padding: 18px; border-radius: 12px; font-size: 20px; font-weight: 600; background: #eef2f6; color: #344054; display: grid; place-items: center; }
		.face-status.success { background: #dcfae6; color: #067647; }
		.face-status.warning { background: #fef0c7; color: #b54708; }
		.face-status.error { background: #fee4e2; color: #b42318; }
		.face-spinner { width: 18px; height: 18px; margin-right: 9px; display: inline-block; vertical-align: -3px; border: 2px solid currentColor; border-right-color: transparent; border-radius: 50%; animation: face-spin .7s linear infinite; }
		@keyframes face-spin { to { transform: rotate(360deg); } }
		@media (max-width: 600px) { .face-guide { inset: 12% 23%; } .face-status { font-size: 17px; } }
	`;
	document.head.appendChild(style);

	root.innerHTML = `
		<div class="face-kiosk">
			<div class="face-camera">
				<video playsinline muted></video>
				<div class="face-guide" aria-hidden="true"></div>
			</div>
			<canvas hidden></canvas>
			<div class="face-status" role="status" aria-live="polite">Starting camera…</div>
		</div>`;

	const video = root.querySelector("video");
	const canvas = root.querySelector("canvas");
	const statusBox = root.querySelector(".face-status");
	let stream = null;
	let timer = null;
	let processing = false;
	let disposed = false;

	function setStatus(message, type = "", busy = false) {
		statusBox.className = `face-status ${type}`;
		statusBox.innerHTML = `${busy ? '<span class="face-spinner"></span>' : ""}<span></span>`;
		statusBox.querySelector("span:last-child").textContent = message;
	}

	function stopCamera() {
		clearTimeout(timer);
		timer = null;
		if (stream) stream.getTracks().forEach((track) => track.stop());
		stream = null;
		video.srcObject = null;
	}

	function scheduleScan(delay = 900) {
		clearTimeout(timer);
		timer = setTimeout(scan, delay);
	}

	async function restartAfterMessage(message, type) {
		stopCamera();
		setStatus(message, type);
		await new Promise((resolve) => setTimeout(resolve, 2000));
		if (!disposed) await startCamera();
	}

	function captureFrame() {
		const width = Math.min(video.videoWidth, 720);
		const height = Math.round((video.videoHeight / video.videoWidth) * width);
		canvas.width = width;
		canvas.height = height;
		canvas.getContext("2d").drawImage(video, 0, 0, width, height);
		return canvas.toDataURL("image/jpeg", 0.86);
	}

	async function scan() {
		if (processing || !stream || video.readyState < 2 || document.hidden) {
			scheduleScan();
			return;
		}
		processing = true;
		const firstImage = captureFrame();
		setStatus(__("Now turn your head to either side."), "warning");
		await new Promise((resolve) => setTimeout(resolve, 1800));
		if (!stream || document.hidden) {
			processing = false;
			return;
		}
		const livenessImage = captureFrame();
		setStatus(__("Verifying live person and recognizing face…"), "", true);

		try {
			const response = await frappe.call({
				method: "pce_sanpra.face_recognition.scan_and_check_in",
				args: { image: firstImage, liveness_image: livenessImage },
				freeze: false,
			});
			const result = response.message || {};
			if (result.status === "checkin_created" || result.status === "checkout_created") {
				await restartAfterMessage(result.message, "success");
			} else if (result.status === "too_soon" || result.status === "checkout_exists") {
				await restartAfterMessage(result.message, "warning");
			} else if (result.status === "not_recognized" || result.status === "spoof_detected") {
				await restartAfterMessage(result.message, "error");
			} else {
				setStatus(result.message || __("Look directly at the camera."));
				scheduleScan(800);
			}
		} catch (error) {
			const message = error?.message || __("Unable to create check-in. Please contact an administrator.");
			await restartAfterMessage(message, "error");
		} finally {
			processing = false;
		}
	}

	async function startCamera() {
		stopCamera();
		setStatus(__("Starting camera…"), "", true);
		try {
			stream = await navigator.mediaDevices.getUserMedia({
				video: { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 960 } },
				audio: false,
			});
			video.srcObject = stream;
			await video.play();
			setStatus(__("Look directly at the camera."));
			scheduleScan(1000);
		} catch (error) {
			setStatus(__("Camera access was blocked. Allow camera permission and reload this page."), "error");
		}
	}

	document.addEventListener("visibilitychange", () => {
		if (document.hidden) stopCamera();
		else if (!disposed) startCamera();
	});
	window.addEventListener("beforeunload", () => {
		disposed = true;
		stopCamera();
	});

	if (!navigator.mediaDevices?.getUserMedia) {
		setStatus(__("This browser does not support camera access. Use HTTPS and a current browser."), "error");
		return;
	}
	startCamera();
});
