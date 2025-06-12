console.log("✅ Druv content script running");

(async () => {
    try {
        const res = await fetch(chrome.runtime.getURL("widget.html"));
        const html = await res.text();
        const wrapper = document.createElement("div");
        wrapper.innerHTML = html;
        document.body.appendChild(wrapper);

        const iconImg = document.querySelector('#druv-launcher img');
        if (iconImg) {
            iconImg.src = chrome.runtime.getURL('content/assets/druv_logo.png');
        }

        const launcher = document.getElementById('druv-launcher');
        const chatbot = document.getElementById('druv-chatbot');
        const closeBtn = document.querySelector('.druv-close');
        const sendBtn = document.getElementById('druv-send');
        const inputBox = document.getElementById('druv-input-box');
        const chatBody = document.getElementById('druv-body');

        document.addEventListener("keydown", (e) => {
            if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "d") {
                e.preventDefault();
                chatbot.classList.toggle("open");
            }
        });

        launcher.addEventListener('click', () => chatbot.classList.toggle('open'));
        closeBtn.addEventListener('click', () => chatbot.classList.remove('open'));

        sendBtn.addEventListener('click', sendMessage);
        inputBox.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });

        async function sendMessage() {
            const message = inputBox.value.trim();
            if (!message) return;

            renderUserBubble(message);
            inputBox.value = '';

            const typing = showTyping();

            const fullText = await extractPageText();

            // ✅ Send as structured JSON
            const payload = {
                input: {
                    question: message,
                    page_content: fullText
                }
            };

            const result = await askBackend(payload);
            renderBotMessage(result);
            chatBody.removeChild(typing);
        }

        async function askBackend(jsonPayload) {
            console.log("✅ Sending to backend:", jsonPayload);
            const res = await fetch("http://127.0.0.1:8000/agent/ask", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(jsonPayload)
            });
            const data = await res.json()
            console.log("✅ Backend response:", data);
            // console.log("✅ Received from backend:", data);
            return data.response
        }


        // Scroll and extract all visible page text
        async function extractPageText() {
            await autoScrollPage();
            await new Promise((r) => setTimeout(r, 500)); // optional wait
            return document.body.innerText || "No visible content found.";
        }

        // Scroll entire page to trigger lazy-loaded content
        async function autoScrollPage() {
            return new Promise((resolve) => {
                let totalHeight = 0;
                const distance = 500;
                const timer = setInterval(() => {
                    const scrollHeight = document.body.scrollHeight;
                    window.scrollBy(0, distance);
                    totalHeight += distance;
                    if (totalHeight >= scrollHeight) {
                        clearInterval(timer);
                        resolve();
                    }
                }, 200);
            });
        }

        function renderUserBubble(msg) {
            const bubble = document.createElement('div');
            bubble.className = 'druv-msg user';
            bubble.innerHTML = `
                <div class="msg-header"><span class="msg-time">${getCurrentTime()}</span></div>
                <div class="msg-content">${msg}</div>`;
            chatBody.appendChild(bubble);
            chatBody.scrollTop = chatBody.scrollHeight;
        }

        function renderBotMessage(msg) {
            const bubble = document.createElement('div');
            bubble.className = 'druv-msg druv';
            bubble.innerHTML = `
                <div class="msg-header"><span class="msg-time">${getCurrentTime()}</span></div>
                <div class="msg-content">${msg}</div>`;
            chatBody.appendChild(bubble);
            chatBody.scrollTop = chatBody.scrollHeight;
        }

        function showTyping() {
            const typing = document.createElement('div');
            typing.className = 'typing-indicator druv';
            typing.innerHTML = '<span></span><span></span><span></span>';
            chatBody.appendChild(typing);
            chatBody.scrollTop = chatBody.scrollHeight;
            return typing;
        }

        function getCurrentTime() {
            const now = new Date();
            let h = now.getHours(), m = now.getMinutes();
            const ampm = h >= 12 ? 'PM' : 'AM';
            h = h % 12 || 12;
            return `${h}:${m.toString().padStart(2, '0')} ${ampm}`;
        }

    } catch (e) {
        console.error("❌ Failed to inject Druv widget.html:", e);
    }
})();
