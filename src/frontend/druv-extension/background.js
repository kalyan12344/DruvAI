// background.js — Druv Extension Backend Messaging Handler

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.cmd === "extractPage") {
        const tabId = sender?.tab?.id;

        // Handle case where sender.tab is unavailable (e.g., from extension popup)
        if (!tabId) {
            console.warn("❌ Could not extract: sender.tab.id is undefined");
            sendResponse({ text: "" });
            return true;
        }

        // Inject script into current tab to extract visible text
        chrome.scripting.executeScript(
            {
                target: { tabId },
                func: () => {
                    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
                    let text = '';
                    while (walker.nextNode()) {
                        const value = walker.currentNode.nodeValue.trim();
                        if (value.length > 30) text += value + '\\n';
                    }
                    return text;
                },
            },
            (results) => {
                if (chrome.runtime.lastError || !results || !results[0]) {
                    console.error("❌ Extraction error:", chrome.runtime.lastError);
                    sendResponse({ text: "" });
                } else {
                    sendResponse({ text: results[0].result });
                }
            }
        );

        return true; // ✅ Keeps the sendResponse port open (important!)
    }
});
