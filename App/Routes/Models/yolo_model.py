from ultralytics import YOLO
import cv2
import numpy as np

class YOLOModel:
    def __init__(self, model_name='yolov8n.pt'):
        # Load YOLOv8 model (downloads automatically on first use)
        self.model = YOLO(model_name)
        # Map COCO class IDs to custom labels (COCO: person=0, car=2, bicycle=1)
        self.label_map = {0: 'person', 2: 'vehicle', 1: 'bike'}

    def infer(self, image):
        # Run inference on the image
        results = self.model(image, conf=0.5)[0]  # Confidence threshold 0.5
        detections = []
        orig_height, orig_width = image.shape[:2]

        # Process detections
        for box in results.boxes:
            class_id = int(box.cls)
            if class_id in self.label_map:  # Only include specified classes
                x_min, y_min, x_max, y_max = map(int, box.xyxy[0])
                conf = float(box.conf)
                detections.append({
                    'label': self.label_map[class_id],
                    'confidence': conf,
                    'bbox': [x_min, y_min, x_max, y_max]
                })

        return detections

    def draw_detections(self, image, detections):
        for detection in detections:
            label = detection['label']
            conf = detection['confidence']
            x_min, y_min, x_max, y_max = detection['bbox']
            # Draw bounding box and label
            color = (0, 255, 0) if label == 'person' else (0, 0, 255) if label == 'vehicle' else (255, 0, 0)
            cv2.rectangle(image, (x_min, y_min), (x_max, y_max), color, 2)
            cv2.putText(image, f'{label}: {conf:.2f}', (x_min, y_min - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        return image