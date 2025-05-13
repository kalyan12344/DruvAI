import { useState, useEffect, useRef } from "react";
import {
  FaMicrophone,
  FaKeyboard,
  FaRobot,
  FaPaperPlane,
} from "react-icons/fa";
import axios from "axios";
import "./voice.css";
import CalendarComponent from "../calender/calender";
import ImportantEmails from "../emails/emails";
import WeatherWidget from "../weather/weather";

const api = axios.create({ baseURL: "http://localhost:5000" });

export default function AIInterface() {
  const [input, setInput] = useState("");
  const [conversation, setConversation] = useState([]);
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => messagesEndRef.current?.scrollIntoView(), [conversation]);

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
      processInput(transcript);
      setIsListening(false);
    };

    recognition.start();
  };

  const processInput = async (userInput) => {
    if (!userInput.trim()) return;
    setIsProcessing(true);
    addToConversation(userInput, false);
    setInput("");

    try {
      const response = await api.post("/process", { input: userInput });
      speak(response.data.response);
    } catch (error) {
      addToConversation("Error processing request", true);
    } finally {
      setIsProcessing(false);
    }
  };

  const speak = (text) => {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.voice = window.speechSynthesis.getVoices()[0];
    window.speechSynthesis.speak(utterance);
    addToConversation(text, true);
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
    <>
      <div className="ai-interface">
        <header
          style={{
            display: "flex",
            flexDirection: "row",
            justifyItems: "center",
            alignItems: "center",
            position: "relative",
            justifyContent: "space-around",
          }}
        >
          <div>
            <h1>
              <FaRobot className="robot-icon" />
              Druv AI
            </h1>
            <p>Your voice-enabled personal assistant</p>
          </div>
          <WeatherWidget />
        </header>
        <div style={{ display: "flex", width: "100vw", flexDirection: "row" }}>
          <div>
            <div className="chat-container">
              {conversation.length > 0 ? (
                conversation.map((msg, i) => (
                  <div
                    key={i}
                    className={`message ${msg.isAI ? "ai" : "user"}`}
                  >
                    <div className="message-content">{msg.text}</div>
                    <div className="message-time">{msg.time}</div>
                  </div>
                ))
              ) : (
                <div className="empty-state">
                  <p>Send a message or click the mic to speak</p>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="input-area">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type or speak your command..."
                onKeyPress={(e) => e.key === "Enter" && processInput(input)}
              />
              <div className="buttons">
                <button
                  onClick={startListening}
                  className={isListening ? "active" : ""}
                  disabled={isProcessing}
                >
                  <FaMicrophone size={20} />
                </button>
                <button
                  onClick={() => processInput(input)}
                  disabled={isProcessing || !input.trim()}
                >
                  <FaPaperPlane size={50} />
                </button>
              </div>
            </div>
          </div>

          <div style={{ width: "600px" }}>
            <CalendarComponent />
          </div>
          <div maxWidth="600px">
            <ImportantEmails />
          </div>
        </div>
      </div>
    </>
  );
}
