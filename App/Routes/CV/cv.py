from flask import Blueprint, request, jsonify
from ..Models.inferences import OpenVINOModel
from ...Utils.preprocess.preprocess import preprocess_image
from PIL import Image
from .config import Config
import io

cv_bp = Blueprint('api', __name__)

model = OpenVINOModel(
    model_xml=Config.MODEL_XML,
    model_bin=Config.MODEL_BIN,
    device=Config.DEVICE
)

@cv_bp.route('/predict', methods=['POST'])
def predict():
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image file provided"}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        image = Image.open(io.BytesIO(file.read()))
        input_data = preprocess_image(image, model.input_shape)
        result = model.predict(input_data)
        
        return jsonify({
            "status": "success",
            **result
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500