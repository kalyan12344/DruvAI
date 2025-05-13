import cv2
import face_recognition
import os

# Create a folder for saving known faces if it doesn't exist
if not os.path.exists("known_faces"):
    os.makedirs("known_faces")

# Open webcam
video_capture = cv2.VideoCapture(0)

while True:
    # Capture frame-by-frame
    ret, frame = video_capture.read()

    if not ret:
        print("Failed to capture frame")
        break

    # Convert frame to RGB for face detection
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Detect faces in the frame
    face_locations = face_recognition.face_locations(rgb_frame)

    # Draw rectangles around detected faces
    for (top, right, bottom, left) in face_locations:
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

    # Show the frame with detected faces
    cv2.imshow("Face Capture", frame)
    key = cv2.waitKey(1) & 0xFF

    # Press 'q' to quit
    if key == ord('q'):
        if face_locations:
            name = input("Enter name: ").strip()  # Get user input
            for i, (top, right, bottom, left) in enumerate(face_locations):
                face = frame[top:bottom, left:right]  # Crop the face
                face_path = f"known_faces/{name}.png"
                cv2.imwrite(face_path, face)
                print(f"Face saved as: {face_path}")
        else:
            print("No face detected! Try again.")
        break        

# Release the webcam and close all windows
video_capture.release()
cv2.destroyAllWindows()
