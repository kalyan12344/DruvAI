document.addEventListener('DOMContentLoaded', function () {
    const launcher = document.getElementById('druv-launcher');
    const chatbot = document.getElementById('druv-chatbot');
    const closeBtn = document.querySelector('.druv-close');
    const sendBtn = document.getElementById('druv-send');
    const inputBox = document.getElementById('druv-input-box');
    const chatBody = document.getElementById('druv-body');

    // Make launcher draggable
    let isDragging = false;
    let offsetX, offsetY;
    let initialX, initialY;

    // Set initial position
    launcher.style.position = 'fixed';
    launcher.style.bottom = '20px';
    launcher.style.right = '20px';

    launcher.addEventListener('mousedown', function (e) {
        // Only start dragging if not clicking a child element
        if (e.target === launcher || e.target === launcher.querySelector('img')) {
            isDragging = true;
            offsetX = e.clientX - launcher.getBoundingClientRect().left;
            offsetY = e.clientY - launcher.getBoundingClientRect().top;
            initialX = e.clientX;
            initialY = e.clientY;
            launcher.style.cursor = 'grabbing';
            e.preventDefault();
        }
    });

    document.addEventListener('mousemove', function (e) {
        if (!isDragging) return;

        // Calculate new position
        const newX = e.clientX - offsetX;
        const newY = e.clientY - offsetY;

        // Apply boundaries if needed (optional)
        launcher.style.left = newX + 'px';
        launcher.style.top = newY + 'px';
        launcher.style.right = 'auto';
        launcher.style.bottom = 'auto';
    });

    document.addEventListener('mouseup', function (e) {
        if (!isDragging) return;

        // Check if it was a click (minimal movement)
        const movedX = Math.abs(e.clientX - initialX);
        const movedY = Math.abs(e.clientY - initialY);

        if (movedX < 5 && movedY < 5) {
            // It's a click, toggle chatbot
            chatbot.classList.toggle('open');
        }

        isDragging = false;
        launcher.style.cursor = 'grab';
    });

    closeBtn.addEventListener('click', function () {
        chatbot.classList.remove('open');
    });

    // Send message function
    function sendMessage() {
        const message = inputBox.value.trim();
        if (message) {
            // Add user message
            const userMsg = document.createElement('div');
            userMsg.className = 'druv-msg user';
            userMsg.innerHTML = `
                <div class="msg-header">
                    <span class="msg-time">${getCurrentTime()}</span>
                </div>
                <div class="msg-content">${message}</div>
            `;
            chatBody.appendChild(userMsg);

            // Clear input
            inputBox.value = '';

            // Show typing indicator
            const typingIndicator = document.createElement('div');
            typingIndicator.className = 'typing-indicator druv';
            typingIndicator.innerHTML = '<span></span><span></span><span></span>';
            chatBody.appendChild(typingIndicator);

            // Scroll to bottom
            chatBody.scrollTop = chatBody.scrollHeight;

            // Simulate response after delay
            setTimeout(function () {
                // Remove typing indicator
                chatBody.removeChild(typingIndicator);

                // Add bot response
                const botMsg = document.createElement('div');
                botMsg.className = 'druv-msg druv';
                botMsg.innerHTML = `
                    <div class="msg-header">
                        <span class="msg-time">${getCurrentTime()}</span>
                    </div>
                    <div class="msg-content">I'm your futuristic AI assistant. How can I help you with your query about "${message}"?</div>
                `;
                chatBody.appendChild(botMsg);

                // Scroll to bottom
                chatBody.scrollTop = chatBody.scrollHeight;
            }, 1500);
        }
    }

    // Send message on button click or Enter key
    sendBtn.addEventListener('click', sendMessage);

    inputBox.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Helper function to get current time
    function getCurrentTime() {
        const now = new Date();
        let hours = now.getHours();
        const minutes = now.getMinutes().toString().padStart(2, '0');
        const ampm = hours >= 12 ? 'PM' : 'AM';
        hours = hours % 12;
        hours = hours ? hours : 12; // the hour '0' should be '12'
        return `${hours}:${minutes} ${ampm}`;
    }
});