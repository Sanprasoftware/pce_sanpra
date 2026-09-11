"""Face recognition endpoint for the employee check-in kiosk."""

from __future__ import annotations

import base64
import binascii
import os
from functools import lru_cache

import cv2
import frappe
import numpy as np
from frappe import _
from frappe.utils import get_datetime, getdate, now_datetime


MAX_IMAGE_BYTES = 5 * 1024 * 1024
MATCH_THRESHOLD = 0.363
MAX_DETECTION_DIMENSION = 640
LIVENESS_THRESHOLD = 0.55
IMAGE_FIELDS = ("left_side", "front_side", "right_side")
CHECKOUT_DELAY_SECONDS = 60 * 60


class FaceRecognitionError(frappe.ValidationError):
	pass


def _model_path(filename: str) -> str:
	return frappe.get_app_path("pce_sanpra", "public", "models", filename)


@lru_cache(maxsize=1)
def _models():
	detector_path = _model_path("face_detection_yunet_2026may.onnx")
	recognizer_path = _model_path("face_recognition_sface_2021dec.onnx")
	if not os.path.isfile(detector_path) or not os.path.isfile(recognizer_path):
		frappe.throw(_("Face recognition models are not installed."), FaceRecognitionError)

	detector = cv2.FaceDetectorYN.create(detector_path, "", (320, 320), 0.8, 0.3, 5000)
	recognizer = cv2.FaceRecognizerSF.create(recognizer_path, "")
	return detector, recognizer


@lru_cache(maxsize=1)
def _anti_spoof_models():
	models = (
		("2.7_80x80_MiniFASNetV2.onnx", 2.7),
		("4_0_0_80x80_MiniFASNetV1SE.onnx", 4.0),
	)
	return [(cv2.dnn.readNetFromONNX(_model_path(filename)), scale) for filename, scale in models]


def _decode_camera_image(image: str) -> np.ndarray:
	if not image or not isinstance(image, str):
		frappe.throw(_("Camera image is required."), FaceRecognitionError)

	encoded = image.split(",", 1)[-1]
	if len(encoded) > (MAX_IMAGE_BYTES * 4 // 3) + 4:
		frappe.throw(_("Camera image is too large."), FaceRecognitionError)
	try:
		raw = base64.b64decode(encoded, validate=True)
	except (ValueError, binascii.Error):
		frappe.throw(_("Invalid camera image."), FaceRecognitionError)
	if len(raw) > MAX_IMAGE_BYTES:
		frappe.throw(_("Camera image is too large."), FaceRecognitionError)

	frame = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
	if frame is None:
		frappe.throw(_("Could not read the camera image."), FaceRecognitionError)
	return frame


def _largest_face(frame: np.ndarray):
	detector, _recognizer = _models()
	height, width = frame.shape[:2]
	detector.setInputSize((width, height))
	_faces_found, faces = detector.detect(frame)
	if faces is None or not len(faces):
		return None
	return max(faces, key=lambda face: float(face[2] * face[3]))


def _prepare_frame(frame: np.ndarray) -> np.ndarray:
	height, width = frame.shape[:2]
	largest_dimension = max(height, width)
	if largest_dimension <= MAX_DETECTION_DIMENSION:
		return frame
	scale = MAX_DETECTION_DIMENSION / largest_dimension
	return cv2.resize(
		frame,
		(round(width * scale), round(height * scale)),
		interpolation=cv2.INTER_AREA,
	)



def _expanded_face_crop(frame: np.ndarray, face: np.ndarray, scale: float) -> np.ndarray:
	height, width = frame.shape[:2]
	x, y, face_width, face_height = (float(value) for value in face[:4])
	scale = min(scale, (width - 1) / face_width, (height - 1) / face_height)
	cx, cy = x + face_width / 2, y + face_height / 2
	crop_width, crop_height = face_width * scale, face_height * scale
	left = max(0, round(cx - crop_width / 2))
	top = max(0, round(cy - crop_height / 2))
	right = min(width, round(cx + crop_width / 2))
	bottom = min(height, round(cy + crop_height / 2))
	return frame[top:bottom, left:right]


def _liveness_score(frame: np.ndarray, face: np.ndarray) -> float:
	predictions = np.zeros(3, dtype=np.float64)
	for model, scale in _anti_spoof_models():
		crop = _expanded_face_crop(frame, face, scale)
		blob = cv2.dnn.blobFromImage(crop, 1.0, (80, 80), swapRB=False, crop=False)
		model.setInput(blob)
		logits = model.forward().reshape(-1)
		exponentials = np.exp(logits - np.max(logits))
		predictions += exponentials / exponentials.sum()
	predictions /= len(_anti_spoof_models())
	return float(predictions[1])

def _feature(frame: np.ndarray) -> np.ndarray | None:
	frame = _prepare_frame(frame)
	face = _largest_face(frame)
	if face is None:
		return None
	_recognizer_detector, recognizer = _models()
	aligned = recognizer.alignCrop(frame, face)
	return recognizer.feature(aligned)


def _file_path(file_url: str) -> str | None:
	if not file_url:
		return None
	file_name = frappe.db.get_value("File", {"file_url": file_url}, "name")
	if not file_name:
		return None
	path = frappe.get_doc("File", file_name).get_full_path()
	return path if os.path.isfile(path) else None


@lru_cache(maxsize=1024)
def _reference_feature(path: str, modified_time: float) -> np.ndarray | None:
	# modified_time is part of the key so replacing an attachment invalidates the cache.
	del modified_time
	frame = cv2.imread(path)
	return _feature(frame) if frame is not None else None


def _find_employee(query_feature: np.ndarray):
	_recognizer_detector, recognizer = _models()
	best_match = None
	best_score = -1.0
	records = frappe.get_all(
		"Employee Face Recognition",
		fields=["employee", "employee_name", *IMAGE_FIELDS],
		filters={"employee": ["is", "set"]},
	)
	for record in records:
		for fieldname in IMAGE_FIELDS:
			path = _file_path(record.get(fieldname))
			if not path:
				continue
			feature = _reference_feature(path, os.path.getmtime(path))
			if feature is None:
				continue
			score = float(recognizer.match(query_feature, feature, cv2.FaceRecognizerSF_FR_COSINE))
			if score > best_score:
				best_score = score
				best_match = record

	if best_match and best_score >= MATCH_THRESHOLD:
		return best_match, best_score
	return None, best_score


def _create_checkin_or_checkout(employee: str, employee_name: str):
	# Serialize scans for this employee so rapid requests cannot create duplicate logs.
	frappe.db.sql("SELECT name FROM `tabEmployee` WHERE name = %s FOR UPDATE", employee)
	current_time = get_datetime(now_datetime()).replace(microsecond=0)
	attendance_date = getdate(current_time)
	logs = frappe.get_all(
		"Employee Checkin",
		filters={
			"employee": employee,
			"time": ("between", [f"{attendance_date} 00:00:00", f"{attendance_date} 23:59:59"]),
		},
		fields=["name", "time", "log_type"],
		order_by="time desc",
		limit=1,
	)

	log_type = "IN"
	if logs:
		latest = logs[0]
		if latest.log_type == "OUT":
			return "checkout_exists", latest, 0
		elapsed_seconds = (current_time - get_datetime(latest.time)).total_seconds()
		if elapsed_seconds < CHECKOUT_DELAY_SECONDS:
			remaining_seconds = max(1, CHECKOUT_DELAY_SECONDS - int(elapsed_seconds))
			return "too_soon", latest, remaining_seconds
		log_type = "OUT"

	checkin = frappe.get_doc(
		{
			"doctype": "Employee Checkin",
			"employee": employee,
			"employee_name": employee_name,
			"time": current_time,
			"log_type": log_type,
			"device_id": "Face Recognition Web Form",
		}
	)
	checkin.insert(ignore_permissions=True)
	status = "checkin_created" if log_type == "IN" else "checkout_created"
	return status, checkin, 0

def _head_yaw(face: np.ndarray) -> float:
	first_eye_x = float(face[4])
	second_eye_x = float(face[6])
	nose_x = float(face[8])
	eye_distance = abs(second_eye_x - first_eye_x)
	if eye_distance < 1:
		return 0.0
	return (nose_x - ((first_eye_x + second_eye_x) / 2)) / eye_distance


@frappe.whitelist()
def scan_and_check_in(image: str, liveness_image: str):
	"""Verify active liveness, recognize the face, and create the employee IN or OUT log."""
	frame = _prepare_frame(_decode_camera_image(image))
	face = _largest_face(frame)
	second_frame = _prepare_frame(_decode_camera_image(liveness_image))
	second_face = _largest_face(second_frame)
	if face is None or second_face is None:
		return {"status": "no_face", "message": _("Keep your face visible during the complete scan.")}

	first_liveness = _liveness_score(frame, face)
	second_liveness = _liveness_score(second_frame, second_face)
	liveness_score = min(first_liveness, second_liveness)
	if liveness_score < LIVENESS_THRESHOLD:
		return {
			"status": "spoof_detected",
			"message": _("Photo or screen detected. A live person must scan at the camera."),
		}

	_recognizer_detector, recognizer = _models()
	query_feature = recognizer.feature(recognizer.alignCrop(frame, face))
	second_feature = recognizer.feature(recognizer.alignCrop(second_frame, second_face))
	same_face_score = float(
		recognizer.match(query_feature, second_feature, cv2.FaceRecognizerSF_FR_COSINE)
	)
	head_turn = abs(_head_yaw(second_face) - _head_yaw(face))
	if same_face_score < MATCH_THRESHOLD or head_turn < 0.18:
		return {
			"status": "spoof_detected",
			"message": _("Liveness check failed. Look forward, then turn your head when asked."),
		}

	employee_record, score = _find_employee(query_feature)
	if not employee_record:
		return {"status": "not_recognized", "message": _("Face not recognized. Please try again.")}

	status, checkin, remaining_seconds = _create_checkin_or_checkout(
		employee_record.employee, employee_record.employee_name
	)
	if status == "too_soon":
		remaining_minutes = max(1, (remaining_seconds + 59) // 60)
		return {
			"status": status,
			"employee": employee_record.employee,
			"employee_name": employee_record.employee_name,
			"remaining_minutes": remaining_minutes,
			"message": _("Please wait {0} minutes before checking out.").format(remaining_minutes),
		}
	if status == "checkout_exists":
		return {
			"status": status,
			"employee": employee_record.employee,
			"employee_name": employee_record.employee_name,
			"checkin": checkin.name,
			"time": checkin.time,
			"message": _("Employee Checkout is already created for {0} today.").format(
				employee_record.employee_name
			),
		}

	action = _("Employee Checkin") if status == "checkin_created" else _("Employee Checkout")

	return {
		"status": status,
		"employee": employee_record.employee,
		"employee_name": employee_record.employee_name,
		"checkin": checkin.name,
		"time": checkin.time,
		"confidence": round(score, 3),
		"liveness": round(liveness_score, 3),
		"message": _("{0} created for {1}.").format(action, employee_record.employee_name),
	}
