import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import VoiceInterface from "./frontend/chatInterface/voice";
import WebcamCapture from "./frontend/login/faceLogin";
function App() {
  return (
    <Router>
      <div className="app">
        <Routes>
          {/* <Route path="/" element={<WebcamCapture />} /> */}
          <Route path="/" element={<VoiceInterface />} />{" "}
        </Routes>
      </div>
    </Router>
  );
}

export default App;
