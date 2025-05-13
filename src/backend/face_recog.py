import cv2
import face_recognition
import numpy as np

# Load stored encodings
known_face_encodings = np.load("encodings.npy", allow_pickle=True)
known_face_names = np.load("names.npy", allow_pickle=True)
print(known_face_names)
# Open webcam
video_capture = cv2.VideoCapture(0)
attendance = {}


while True:
    # Capture frame-by-frame
    ret, frame = video_capture.read()
    
    if not ret:
        print("Failed to capture frame")
        break

    # Convert frame to RGB (face_recognition uses RGB format)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Detect face locations and encode them
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        # Compare detected face with stored encodings
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        
        # Set default name as "Unknown"
        name = "Unknown"

        # Find the best match
        if len(face_distances) > 0:
            best_match_index = np.argmin(face_distances)  # Get the index of the best match
            if matches[best_match_index]:
                name = known_face_names[best_match_index]  # Get the corresponding name
                print(name)

        if name not in attendance:
            attendance[str(name)] = "present"
        # Draw rectangle around the face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

        # Display the name below the face
        cv2.putText(frame, name, (left, bottom + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # Show the frame with recognized faces
    cv2.imshow("Face Recognition", frame)
    key = cv2.waitKey(1) & 0xFF

    # Press 'q' to quit
    if key == ord('q'):
        print(attendance)
        break
    if key == ord('c'):
        print(f"matches ${matches}")
        print(f"face distances ${face_distances}")


# Release the webcam and close all windows
video_capture.release()
cv2.destroyAllWindows()
