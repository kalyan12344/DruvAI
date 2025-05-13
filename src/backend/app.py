from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import face_recognition
import numpy as np
import base64
import io
from PIL import Image

app = Flask(__name__)
CORS(app)

# Load stored encodings
known_face_encodings = np.load("encodings.npy", allow_pickle=True)
known_face_names = np.load("names.npy", allow_pickle=True)

@app.route("/recognize", methods=["POST"])
def recognize_face():
    data = request.json
    image_data = data["image"].split(",")[1]  # Remove base64 prefix
    decoded_image = base64.b64decode(image_data)

    # Convert to OpenCV format
    image = np.array(Image.open(io.BytesIO(decoded_image)))
    rgb_frame = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Detect face and encode
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)

        if len(face_distances) > 0:
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                return jsonify({"name": known_face_names[best_match_index]})

    return jsonify({"name": "Unknown"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
