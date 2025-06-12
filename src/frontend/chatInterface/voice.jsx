import { useState, useEffect, useRef } from "react";
import {
  FaMicrophone,
  FaRobot,
  FaPaperPlane,
} from "react-icons/fa";
import axios from "axios";
import "./voice.css";
// import CalendarComponent from "../calender/calender"; // Assuming not used directly in this file for this task
// import ImportantEmails from "../emails/emails"; // Assuming not used directly
// import WeatherWidget from "../weather/weather"; // Assuming not used directly
import { motion } from "framer-motion";

const api = axios.create({ baseURL: "http://localhost:8000/agent" });

export default function AIInterface() {
  const [input, setInput] = useState("");
  const [conversation, setConversation] = useState([]);
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const messagesEndRef = useRef(null);
  const [pastedImage, setPastedImage] = useState(null);

  useEffect(() => messagesEndRef.current?.scrollIntoView(), [conversation]);

  const constructPayload = (currentQuestion) => {
    const pageContentForAgent = window.currentPageTextForAgent || null; // YOU MUST REPLACE THIS PLACEHOLDER

    let payload;
    if (pageContentForAgent && pageContentForAgent.trim() !== "") {
      payload = {
        input: {
          question: currentQuestion,
          page_content: pageContentForAgent
        }
      };
      console.log("Sending structured input (question + page_content):", payload);
    } else {
      payload = {
        input: currentQuestion
      };
      console.log("Sending simple string input:", payload);
    }
    return payload;
  };

  const handleSend = async () => {
    const currentQuestion = input.trim();
    if (isProcessing || !currentQuestion) return;

    setIsProcessing(true);
    setInput("");
    addToConversation(currentQuestion, false);

    const payload = constructPayload(currentQuestion);

    try {
      const response = await api.post("/ask", payload);
      console.log("Response from server:", response);
      const aiReply = response.data.response || "⚠️ No answer received from agent.";
      console.log("AI Reply:", aiReply);
      speak(aiReply);
    } catch (err) {
      console.error("Error sending request:", err);
      let errorMessage = "❌ Error processing your request.";
      if (err.response && err.response.data) {
        if (err.response.data.detail) {
          if (Array.isArray(err.response.data.detail)) {
            errorMessage = `❌ Backend Error: ${err.response.data.detail.map(d => d.msg || d.message || JSON.stringify(d)).join(', ')}`;
          } else if (typeof err.response.data.detail === 'string') {
            errorMessage = `❌ Backend Error: ${err.response.data.detail}`;
          }
        } else if (err.response.data.response) {
          errorMessage = `❌ Backend Error: ${err.response.data.response}`;
        }
      } else if (err.message) {
        errorMessage = `❌ Network or other error: ${err.message}`;
      }
      addToConversation(errorMessage, true);
    } finally {
      setIsProcessing(false);
    }
  };

  const startListening = () => {
    const recognition = new (window.SpeechRecognition ||
      window.webkitSpeechRecognition)();
    recognition.lang = "en-US";
    recognition.interimResults = false;

    recognition.onstart = () => {
      setIsListening(true);
      setInput("Listening...");
    };

    recognition.onresult = (e) => {
      const transcript = e.results[0][0].transcript;
      setInput(transcript);
      handleSendFromTranscript(transcript);
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error', event.error);
      setInput(prevInput => prevInput === "Listening..." ? "" : prevInput);
      addToConversation(`⚠️ Mic error: ${event.error}`, true);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
      if (input === "Listening...") {
        setInput("");
      }
    };

    recognition.start();
  };

  const handleSendFromTranscript = async (transcript) => {
    const currentQuestion = transcript.trim();
    if (!currentQuestion) {
      setIsProcessing(false); // Ensure processing is false if transcript is empty
      return;
    }

    // Note: Not calling addToConversation here as handleSend/speak will do it if successful
    // Setting isProcessing true should happen if we decide to proceed
    setIsProcessing(true);
    // setInput was already set by onresult in startListening

    const payload = constructPayload(currentQuestion);

    try {
      const response = await api.post("/ask", payload);
      console.log("Response from server (voice):", response);
      const aiReply = response.data.response || "⚠️ No answer received from agent.";
      console.log("AI Reply (voice):", aiReply);
      speak(aiReply); // This will call addToConversation for the AI
    } catch (error) {
      console.error("Error processing voice request:", error);
      let errorMessage = "❌ Error processing your voice request.";
      if (error.response && error.response.data) {
        if (error.response.data.detail) {
          if (Array.isArray(error.response.data.detail)) {
            errorMessage = `❌ Backend Error: ${error.response.data.detail.map(d => d.msg || d.message || JSON.stringify(d)).join(', ')}`;
          } else if (typeof error.response.data.detail === 'string') {
            errorMessage = `❌ Backend Error: ${error.response.data.detail}`;
          }
        } else if (error.response.data.response) {
          errorMessage = `❌ Backend Error: ${error.response.data.response}`;
        }
      } else if (error.message) {
        errorMessage = `❌ Network or other error: ${error.message}`;
      }
      addToConversation(errorMessage, true);
    } finally {
      setIsProcessing(false);
    }
  };

  const speak = (text) => {
    const utterance = new SpeechSynthesisUtterance(text);
    const voices = window.speechSynthesis.getVoices();
    if (voices.length > 0) {
      utterance.voice = voices.find(voice => voice.lang === "en-US") || voices[0];
    }
    window.speechSynthesis.speak(utterance);
    addToConversation(text, true);
  };

  const handlePaste = (e) => {
    const items = e.clipboardData?.items;
    if (!items) return;

    for (let item of items) {
      if (item.type.indexOf("text/plain") !== -1) {
        item.getAsString((text) => {
          console.log("Pasted text:", text);
          // YOU NEED TO DECIDE: How to handle pasted text.
          // Option A: Set as input for question: setInput(text);
          // Option B: Set as page context (needs UI/logic): window.currentPageTextForAgent = text;
        });
      } else if (item.type.indexOf("image") !== -1) {
        const blob = item.getAsFile();
        if (blob) {
          const imageURL = URL.createObjectURL(blob);
          setPastedImage({ blob, preview: imageURL });
          e.preventDefault();
          break;
        }
      }
    }
  };

  const handleImageUpload = async (file) => {
    if (!file) return;
    setIsProcessing(true);
    addToConversation("📤 Uploading your schedule image...", false);

    const formData = new FormData();
    formData.append("image", file);

    try {
      const response = await api.post("/api/schedule/image-upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      const msg = response.data.message || "✅ Image processed.";
      speak(msg);
    } catch (error) {
      console.error("Upload error:", error);
      addToConversation("❌ Failed to upload or process image", true);
    } finally {
      setIsProcessing(false);
    }
  };

  const addToConversation = (text, isAI) => {
    setConversation((prev) => [
      ...prev,
      {
        text,
        isAI,
        time: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      },
    ]);
  };

  return (
    <div className="dashboard-ai-interface">
      <motion.header
        className="ai-header"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="ai-title">
          <FaRobot className="robot-icon" />
          <h1>Druv AI</h1>
        </div>
        <p className="ai-subtitle">Your voice-enabled personal assistant</p>
      </motion.header>

      <div className="ai-chat-container" style={{ overflowY: "scroll", maxHeight: "80%" }}>
        {conversation.length > 0 ? (
          conversation.map((msg, i) => (
            <motion.div
              key={i}
              className={`ai-message ${msg.isAI ? "ai" : "user"}`}
              initial={{ opacity: 0, x: msg.isAI ? 20 : -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3 }}
            >
              <div className="message-content">{msg.text}</div>
              <div className="message-time">{msg.time}</div>
            </motion.div>
          ))
        ) : (
          <motion.div
            className="ai-empty-state"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <p>Send a message or click the mic to speak</p>
          </motion.div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <motion.div
        className="ai-input-area ai-input-preview-wrapper"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        {pastedImage && (
          <div className="pasted-image-preview">
            <img src={pastedImage.preview} alt="Pasted" />
            <button onClick={() => setPastedImage(null)} className="remove-image-btn">x</button>
          </div>
        )}

        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type or speak your command..."
          onKeyPress={(e) => e.key === "Enter" && handleSend()}
          onPaste={handlePaste}
          className="ai-input"
        />

        <div className="ai-buttons">
          <motion.button
            onClick={startListening}
            className={`ai-mic-button ${isListening ? "active" : ""}`}
            disabled={isProcessing}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <FaMicrophone />
          </motion.button>
          <motion.button
            onClick={handleSend}
            disabled={isProcessing || (!input.trim() && !pastedImage)}
            className="ai-send-button"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <FaPaperPlane />
          </motion.button>
        </div>
      </motion.div>
    </div>
  );
}