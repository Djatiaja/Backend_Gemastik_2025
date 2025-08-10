import openvino as ov
import numpy as np
from PIL import Image
import cv2

class OpenVINOModel:
    def __init__(self, xml_path, bin_path, device='CPU'):
        self.core = ov.Core()
        self.model = self.core.read_model(model=xml_path, weights=bin_path)
        self.compiled_model = self.core.compile_model(self.model, device_name=device)
        self.input_layer = self.compiled_model.input(0)
        self.output_layer = self.compiled_model.output(0)
        self.input_shape = self.input_layer.shape  # e.g., [1, 3, 768, 1024]

    def preprocess_image(self, image):
        target_height, target_width = self.input_shape[2], self.input_shape[3]
        img = cv2.resize(image, (target_width, target_height))
        img = img.astype(np.float32)
        img = img.transpose((2, 0, 1))  # HWC to CHW
        img = np.expand_dims(img, axis=0)  # Add batch dimension
        img = img / 255.0  
        return img

    def postprocess_detections(self, detections, conf_threshold=0.5, image_shape=None):
        detections = detections[0][0]  # Remove batch and extra dims
        results = []
        labels = {1: 'person', 2: 'vehicle', 3: 'bike'}
        orig_height, orig_width = image_shape
        target_height, target_width = self.input_shape[2], self.input_shape[3]
        for detection in detections:
            conf = detection[2]
            if conf > conf_threshold:
                # Scale bounding box back to original image size
                x_min = int(detection[3] * orig_width / target_width)
                y_min = int(detection[4] * orig_height / target_height)
                x_max = int(detection[5] * orig_width / target_width)
                y_max = int(detection[6] * orig_height / target_height)
                result = {
                    'label': labels.get(int(detection[1]), 'unknown'),
                    'confidence': float(conf),
                    'bbox': [x_min, y_min, x_max, y_max]
                }
                results.append(result)
        return results

    def draw_detections(self, image, detections):
        for detection in detections:
            label = detection['label']
            conf = detection['confidence']
            x_min, y_min, x_max, y_max = detection['bbox']
            color = (0, 255, 0) if label == 'person' else (0, 0, 255) if label == 'vehicle' else (255, 0, 0)
            cv2.rectangle(image, (x_min, y_min), (x_max, y_max), color, 2)
            cv2.putText(image, f'{label}: {conf:.2f}', (x_min, y_min - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        return image

    def infer(self, image):
        input_data = self.preprocess_image(image)
        result = self.compiled_model([input_data])[self.output_layer]
        detections = self.postprocess_detections(result, image_shape=image.shape[:2])
        return detections