from openvino.runtime import Core
import numpy as np

class OpenVINOModel:
    def __init__(self, model_xml, model_bin, device="CPU"):
        self.core = Core()
        # Read model (IR format: .xml + .bin)
        self.model = self.core.read_model(model=model_xml, weights=model_bin)
        # Compile the model for the target device
        self.compiled_model = self.core.compile_model(self.model, device)
        
        # Get input and output layer info
        self.input_layer = self.model.inputs[0]
        self.output_layer = self.model.outputs[0]
        self.input_shape = self.input_layer.shape

    def predict(self, input_data):
        # Ensure input is in the correct shape
        if input_data.shape != tuple(self.input_shape):
            raise ValueError(f"Expected input shape {self.input_shape}, got {input_data.shape}")
        
        # Run inference
        result = self.compiled_model([input_data])[self.output_layer]
        
        # Get predicted class and confidence
        predicted_class = int(np.argmax(result[0]))
        confidence = float(np.max(result[0]))
        return {"predicted_class": predicted_class, "confidence": confidence}

