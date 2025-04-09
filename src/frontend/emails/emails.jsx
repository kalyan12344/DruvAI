import { useState, useEffect, useRef } from "react";
import { FaArrowUp, FaArrowDown } from "react-icons/fa";
import axios from "axios";
import "../emails/emails.css"; // Adjust path if needed

export default function ImportantEmails() {
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isMobile, setIsMobile] = useState(window.visualViewport.width < 1000);
  const [showPanel, setShowPanel] = useState(
    window.visualViewport.width >= 1000
  );
  const [lastUpdated, setLastUpdated] = useState(null);
  const scrollRef = useRef(null);

  useEffect(() => {
    const fetchEmails = () => {
      setLoading(true);
      axios
        .get("http://localhost:5000/api/emails/important")
        .then((res) => {
          console.log("Fetched emails:", res.data.important);
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

    return () => clearInterval(intervalId);
  }, []);

  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      if (!mobile) setShowPanel(true);
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
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
      <div className="floating-icon" onClick={() => setShowPanel(true)}>
        📩
      </div>
    );
  }

  return (
    <div
      className={`email-widget ${isMobile ? "mobile" : ""}`}
      style={{ width: "600px" }}
    >
      {isMobile && (
        <button className="close-btn" onClick={() => setShowPanel(false)}>
          ❌
        </button>
      )}

      <div className="header-row">
        <h3>📬 Important Emails</h3>
        <div className="scroll-buttons">
          <button onClick={() => scroll("up")}>
            <FaArrowUp />
          </button>
          <button onClick={() => scroll("down")}>
            <FaArrowDown />
          </button>
        </div>
      </div>

      <div className="email-scroll-container" ref={scrollRef}>
        {loading ? (
          <p>⏳ Loading important emails...</p>
        ) : emails.length === 0 ? (
          <p>📭 No important emails found.</p>
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
          <small>🕒 Last updated: {lastUpdated}</small>
        </div>
      )}
    </div>
  );
}
