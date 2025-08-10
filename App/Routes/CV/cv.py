import time
from flask import Blueprint, Response, jsonify, request
import cv2
import numpy as np
from ultralytics import YOLO
from openvino.runtime import Core
import logging
from dataclasses import dataclass
from typing import Optional
import yaml

# =================== CONFIGURATION CLASS ===================
@dataclass
class Config:
    use_camera: bool = True
    camera_id: int = 0
    video_path: str = r"C:\Users\LENOVO\Downloads\1023-142621257_small.mp4"
    yolo_model_path: str = r"App/Routes/CV/yolo11n_openvino_model"
    midas_model_xml: str = r"App/Routes/CV/yolo11n_openvino_model/yolo11n.xml"
    confidence_threshold: float = 0.6
    blur_kernel: tuple = (5, 5)

# =================== LOGGER SETUP =========================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# =================== OBJECT DETECTOR CLASS =================
class ObjectDetector:
    def __init__(self, config: Config):
        self.config = config
        self.core = Core()
        self.yolo_model = None
        self.compiled_midas = None
        self.colors_yolo = None
        self.fps = 0
        self.frame_count = 0
        self.start_time = None

    def initialize(self) -> bool:
        try:
            self.yolo_model = YOLO(self.config.yolo_model_path, task="detect")
            self.colors_yolo = np.random.randint(0, 255, size=(len(self.yolo_model.names), 3), dtype="uint8")

            midas_model = self.core.read_model(self.config.midas_model_xml)
            self.compiled_midas = self.core.compile_model(midas_model, "CPU")

            logger.info("Successfully initialized YOLO and MiDaS models")
            return True
        except Exception as e:
            logger.error(f"Initialization failed: {str(e)}")
            return False

    def estimate_depth(self, image: np.ndarray) -> np.ndarray:
        try:
            img = cv2.resize(image, (256, 256))
            img = img.astype(np.float32) / 255.0
            img = img.transpose(2, 0, 1)[np.newaxis, :]
            result = self.compiled_midas([img])[self.compiled_midas.output(0)]
            depth_map = result[0, 0]
            return cv2.resize(depth_map, (image.shape[1], image.shape[0]))
        except Exception as e:
            logger.error(f"Depth estimation failed: {str(e)}")
            return np.zeros((image.shape[0], image.shape[1]))

    def process_frame(self, frame: np.ndarray) -> tuple[np.ndarray, dict, list]:
        counts = {}
        depth_map = self.estimate_depth(frame)
        frame_blur = cv2.GaussianBlur(frame.copy(), self.config.blur_kernel, 0)

        yolo_results = self.yolo_model(frame_blur)[0]
        detections = []
        for box in yolo_results.boxes:
            cls_id = int(box.cls)
            conf = float(box.conf)
            if conf < self.config.confidence_threshold:
                continue

            label = self.yolo_model.names.get(cls_id, f"id_{cls_id}")
            if label.lower() in ["cell phone"]:
                continue

            color = [int(c) for c in self.colors_yolo[cls_id % len(self.colors_yolo)]]
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            # Calculate proximity data
            center_x = (x1 + x2) / 2
            frame_center_x = frame.shape[1] / 2
            distance_x = abs(center_x - frame_center_x)
            sim_depth_x = max(0.0, min(1.0, 1 - (distance_x / frame_center_x)))
            bottom_y = max(y1, y2)
            sim_depth_y = max(0.0, min(1.0, bottom_y / frame.shape[0]))
            sim_depth_gradient = (sim_depth_x + sim_depth_y) / 2
            direction = "KIRI" if (center_x - frame_center_x) < 0 else "KANAN"
            warning_text = f"⚠ Dekat! Arah: {direction}" if sim_depth_gradient > 0.85 else ""
            proximity = "Dekat" if sim_depth_gradient > 0.85 else "Jauh"

            self._draw_detection(frame, x1, y1, x2, y2, label, conf, color, depth_map, counts)
            detections.append({
                'label': label,
                'confidence': conf,
                'bbox': [x1, y1, x2, y2],
                'depth': float(np.median(depth_map[y1:y2, x1:x2]) if depth_map[y1:y2, x1:x2].size > 0 else 0),
                'sim_depth_x': sim_depth_x,
                'sim_depth_y': sim_depth_y,
                'sim_depth_gradient': sim_depth_gradient,
                'direction': direction,
                'warning': warning_text,
                'proximity': proximity
            })

        return frame, counts, detections

    def _draw_detection(self, frame: np.ndarray, x1: int, y1: int, x2: int, y2: int,
                    label: str, conf: float, color: list, depth_map: np.ndarray, counts: dict):
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # SimDepth X (semakin dekat ke tengah sumbu X)
        center_x = (x1 + x2) / 2
        frame_center_x = frame.shape[1] / 2
        distance_x = abs(center_x - frame_center_x)
        sim_depth_x = 1 - (distance_x / frame_center_x)
        sim_depth_x = max(0.0, min(1.0, sim_depth_x))

        # SimDepth Y (semakin ke bawah sumbu Y dianggap makin dekat)
        bottom_y = max(y1, y2)
        sim_depth_y = bottom_y / frame.shape[0]
        sim_depth_y = max(0.0, min(1.0, sim_depth_y))

        # Gradien gabungan antara X dan Y
        sim_depth_gradient = (sim_depth_x + sim_depth_y) / 2

        # Arah objek berdasarkan posisi X
        direction = "KIRI" if (center_x - frame_center_x) < 0 else "KANAN"

        # Tampilkan semua nilai
        cv2.putText(frame, f"SimDepth X: {sim_depth_x:.2f}", (x1, y2 + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(frame, f"SimDepth Y: {sim_depth_y:.2f}", (x1, y2 + 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(frame, f"SimDepth Grad: {sim_depth_gradient:.2f}", (x1, y2 + 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        # Threshold peringatan
        if sim_depth_gradient > 0.85:
            warning_text = f"⚠ Dekat! Arah: {direction}"
            (text_w, text_h), _ = cv2.getTextSize(warning_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)

            # Posisi di atas box (tepat di atas y1)
            padding = 5
            text_x = x1
            text_y = y1 - 10

            # Pastikan tidak keluar dari frame atas
            if text_y - text_h - padding < 0:
                text_y = y1 + text_h + 10  # tampilkan di dalam box jika terlalu dekat dengan atas

            # Gambar kotak background (merah)
            cv2.rectangle(frame,
                        (text_x - padding, text_y - text_h - padding),
                        (text_x + text_w + padding, text_y + padding),
                        (0, 0, 255), -1)

            # Tulis teks peringatan (putih)
            cv2.putText(frame, warning_text, (text_x, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    def display_counts(self, frame: np.ndarray, counts: dict):
        if self.start_time is None:
            self.start_time = time.time()

        y_offset = 20
        for label, count in counts.items():
            cv2.putText(frame, f"{label}: {count}", (10, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            y_offset += 20

        self.frame_count += 1
        elapsed_time = time.time() - self.start_time
        if elapsed_time > 1:
            self.fps = self.frame_count / elapsed_time
            self.frame_count = 0
            self.start_time = time.time()

        cv2.putText(frame, f"FPS: {self.fps:.2f}", (10, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

# =================== FLASK BLUEPRINT ===================
inference_bp = Blueprint('inference', __name__, template_folder='../../templates')

def load_config(config_path: str = "config.yaml") -> Config:
    try:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        return Config(**config_data)
    except FileNotFoundError:
        logger.warning("Config file not found, using default configuration")
        return Config()
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        return Config()

# Initialize detector
config = load_config()
detector = ObjectDetector(config)
if not detector.initialize():
    logger.error("Failed to initialize ObjectDetector")

def generate_frames():
    cap = cv2.VideoCapture(config.camera_id if config.use_camera else config.video_path)
    if not cap.isOpened():
        logger.error(f"Failed to open {'camera' if config.use_camera else config.video_path}")
        return
    try:
        while True:
            success, frame = cap.read()
            if not success:
                logger.info("Finished processing video")
                break

            frame, counts, _ = detector.process_frame(frame)
            detector.display_counts(frame, counts)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    except Exception as e:
        logger.error(f"Error in generate_frames: {str(e)}")
    finally:
        cap.release()

@inference_bp.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@inference_bp.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    try:
        image_file = request.files['image']
        file_bytes = np.frombuffer(image_file.read(), np.uint8)
        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        _, _, detections = detector.process_frame(image)
        logger.info(f"Detections: {detections}")

        return jsonify({'detections': detections})
    except Exception as e:
        return jsonify({'error': str(e)}), 500