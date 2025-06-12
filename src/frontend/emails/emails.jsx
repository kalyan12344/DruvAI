import { useState, useEffect, useRef } from "react";
import { FaArrowUp, FaArrowDown, FaTimes, FaEnvelope } from "react-icons/fa";
import axios from "axios";
import "../emails/emails.css";

export default function ImportantEmails() {
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 1000);
  const [showPanel, setShowPanel] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const scrollRef = useRef(null);

  useEffect(() => {
    const fetchEmails = () => {
      setLoading(true);
      axios
        .get("http://localhost:5001/api/emails/important")
        .then((res) => {
          setEmails(res.data.important || []);
          setLastUpdated(new Date().toLocaleTimeString());
          setLoading(false);
        })
        .catch((error) => {
          console.error("Error fetching emails:", error);
          setEmails(["❌ Failed to load important emails."]);
          setLoading(false);
        });
    };

    // Initial fetch
    fetchEmails();

    // Poll every 60 seconds
    const intervalId = setInterval(fetchEmails, 60000);

    // Handle resize
    const handleResize = () => {
      const mobile = window.innerWidth < 1000;
      setIsMobile(mobile);
      if (!mobile) setShowPanel(true);
    };

    window.addEventListener("resize", handleResize);

    return () => {
      clearInterval(intervalId);
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  const scroll = (direction) => {
    const container = scrollRef.current;
    if (container) {
      const scrollAmount = 150;
      container.scrollBy({
        top: direction === "up" ? -scrollAmount : scrollAmount,
        behavior: "smooth",
      });
    }
  };

  if (isMobile && !showPanel) {
    return (
      <div
        className="floating-email-icon"
        onClick={() => setShowPanel(true)}
        title="View important emails"
      >
        <FaEnvelope className="envelope-icon" />
        {emails.length > 0 && (
          <span className="email-badge">{emails.length}</span>
        )}
      </div>
    );
  }

  return (
    <div className={`email-widget ${isMobile ? "mobile" : ""}`}>
      {isMobile && (
        <button
          className="close-btn"
          onClick={() => setShowPanel(false)}
          aria-label="Close email panel"
        >
          <FaTimes />
        </button>
      )}

      <div className="header-row">
        <h3>
          <FaEnvelope className="header-icon" /> Important Emails
        </h3>
        <div className="scroll-buttons">
          <button onClick={() => scroll("up")} aria-label="Scroll up">
            <FaArrowUp />
          </button>
          <button onClick={() => scroll("down")} aria-label="Scroll down">
            <FaArrowDown />
          </button>
        </div>
      </div>

      <div className="email-scroll-container" ref={scrollRef}>
        {loading ? (
          <div className="loading-state">
            <div className="loading-spinner"></div>
            <p>Loading important emails...</p>
          </div>
        ) : emails.length === 0 ? (
          <p className="empty-state">No important emails found.</p>
        ) : (
          emails.map((email, index) => (
            <div className="email-card" key={index}>
              {email}
            </div>
          ))
        )}
      </div>

      {lastUpdated && (
        <div className="last-updated">
          <small>Last updated: {lastUpdated}</small>
        </div>
      )}
    </div>
  );
}
