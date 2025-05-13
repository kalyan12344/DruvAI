import face_recognition
import os
import numpy as np

# Directory containing known faces
known_faces_dir = "known_faces"
face_encodings_list = []
face_names = []

for filename in os.listdir(known_faces_dir):
    if filename.endswith(".jpg") or filename.endswith(".png"):
        filepath = os.path.join(known_faces_dir, filename)

        # Load and encode face
        image = face_recognition.load_image_file(filepath)
        encodings = face_recognition.face_encodings(image)

        if len(encodings) > 0:
            face_encodings_list.append(encodings[0])  # Save encoding
            face_names.append(os.path.splitext(filename)[0])  # Use filename as name
            print(f"Encoded: {filename}")
        else:
            print(f"No face found in {filename}")

print(f"\nTotal Encoded Faces: {len(face_encodings_list)}")

# Save encodings for later use
np.save("encodings.npy", face_encodings_list)
np.save("names.npy", face_names)

print("Encodings saved successfully!")


loaded_encodings = np.load("encodings.npy", allow_pickle=True)
loaded_names = np.load("names.npy", allow_pickle=True)

print("Loaded Encodings:", loaded_encodings)
print("Loaded Names:", loaded_names)