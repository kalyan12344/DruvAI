import React, { useEffect, useRef, useState } from "react";
import Webcam from "react-webcam";
import axios from "axios";
import { useNavigate } from "react-router-dom";

const WebcamCapture = () => {
  const webcamRef = useRef(null);
  const [spoken, setSpoken] = useState(false);
  const navigate = useNavigate();

  const speak = (text) => {
    const synth = window.speechSynthesis;
    const utter = new SpeechSynthesisUtterance(text);
    synth.speak(utter);
  };

  useEffect(() => {
    if (!spoken) {
      speak("Welcome! Please show your face.");
      setTimeout(capture, 2500); // allow webcam to initialize
      setSpoken(true);
    }
  }, [spoken]);

  const capture = async () => {
    if (webcamRef.current) {
      const imageSrc = webcamRef.current.getScreenshot();

      try {
        const response = await axios.post("http://localhost:5000/recognize", {
          image: imageSrc,
        });

        const name = response.data.name;

        if (name === "Kalyan" || name === "kkk" || name === "kalyan2") {
          speak("Welcome Kalyan");
          setTimeout(() => navigate("/voice"), 1500); // Redirect after greeting
        } else {
          speak("Sorry, only Kalyan can access me.");
        }
      } catch (error) {
        console.error("Face recognition failed:", error);
        speak("Something went wrong while recognizing.");
      }
    }
  };

  return (
    <div style={{ textAlign: "center", marginTop: "20px" }}>
      <h2>Druv Face Login</h2>
      <Webcam
        ref={webcamRef}
        screenshotFormat="image/png"
        width={300}
        height={300}
      />
      <br />
      <button onClick={capture} style={{ marginTop: "10px" }}>
        Retry Recognition
      </button>
    </div>
  );
};

export default WebcamCapture;
