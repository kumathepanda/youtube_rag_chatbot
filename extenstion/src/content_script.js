// --- Constants ---
const API_BASE_URL = "http://127.0.0.1:5000";

// --- Main Execution ---
let currentVideoId = null;

// Function to inject the UI
async function injectUI() {
    try {
        // Fetch the HTML for the chat UI
        const response = await fetch(chrome.runtime.getURL('src/injected_ui.html'));
        const html = await response.text();
        
        // Create a container for our UI and inject it
        const uiContainer = document.createElement('div');
        uiContainer.innerHTML = html;
        document.body.appendChild(uiContainer);

        // Now that the UI is in the DOM, add event listeners
        addEventListeners();
        
        // Initial check for video status
        checkForVideo();

    } catch (error) {
        console.error("YT RAG Chatbot: Error injecting UI:", error);
    }
}

// --- Event Listeners ---
function addEventListeners() {
    document.getElementById('rag-chat-toggle-btn').addEventListener('click', toggleChatWindow);
    document.getElementById('rag-process-video-btn').addEventListener('click', handleProcessVideo);
    document.getElementById('rag-chat-form').addEventListener('submit', handleSendMessage);
}

// --- UI Logic ---
function toggleChatWindow() {
    const container = document.getElementById('rag-chat-container');
    container.classList.toggle('minimized');
}

function displayMessage(text, sender) {
    const messagesContainer = document.getElementById('rag-chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `rag-chat-message ${sender}`;
    messageDiv.textContent = text;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight; // Auto-scroll
}

function showLoadingIndicator() {
    const messagesContainer = document.getElementById('rag-chat-messages');
    // Remove initial view if it exists
    const initialView = document.getElementById('rag-initial-view');
    if(initialView) initialView.style.display = 'none';

    // Check if a loading indicator already exists
    if (messagesContainer.querySelector('.loading')) return;

    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'rag-chat-message bot loading';
    loadingDiv.innerHTML = '<div class="dot-flashing"></div>';
    messagesContainer.appendChild(loadingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function hideLoadingIndicator() {
    const loadingIndicator = document.querySelector('.rag-chat-message.loading');
    if (loadingIndicator) {
        loadingIndicator.remove();
    }
}

function updateStatusText(text) {
    document.getElementById('rag-status-text').textContent = text;
}

function activateChat() {
    document.getElementById('rag-initial-view').style.display = 'none';
    const input = document.getElementById('rag-chat-input');
    const sendBtn = document.getElementById('rag-chat-send-btn');
    input.disabled = false;
    sendBtn.disabled = false;
    displayMessage("This video is ready. Ask me anything!", "bot");
}


// --- API Communication ---
async function checkVideoStatus(videoId) {
    try {
        const response = await fetch(`${API_BASE_URL}/video_status/${videoId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        
        if (data.status === 'processed') {
            activateChat();
        } else {
            document.getElementById('rag-process-video-btn').disabled = false;
            updateStatusText("This video hasn't been processed yet.");
        }
    } catch (error) {
        console.error("YT RAG Chatbot: Error checking video status:", error);
        updateStatusText("Could not connect to the server.");
    }
}

async function handleProcessVideo() {
    if (!currentVideoId) return;

    const processBtn = document.getElementById('rag-process-video-btn');
    processBtn.disabled = true;
    updateStatusText("Processing video... this may take a moment.");

    try {
        const response = await fetch(`${API_BASE_URL}/process-video`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ videoId: currentVideoId })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        updateStatusText("Processing complete!");
        activateChat();

    } catch (error) {
        console.error("YT RAG Chatbot: Error processing video:", error);
        updateStatusText("Failed to process the video. Please try again.");
        processBtn.disabled = false;
    }
}

async function handleSendMessage(event) {
    event.preventDefault();
    const input = document.getElementById('rag-chat-input');
    const question = input.value.trim();

    if (!question || !currentVideoId) return;

    displayMessage(question, 'user');
    input.value = '';
    showLoadingIndicator();

    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ videoId: currentVideoId, question: question })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        hideLoadingIndicator();
        displayMessage(data.answer, 'bot');

    } catch (error) {
        console.error("YT RAG Chatbot: Error sending message:", error);
        hideLoadingIndicator();
        displayMessage("Sorry, I couldn't get a response. Please check the server.", "bot");
    }
}

// --- YouTube Page Integration ---
function checkForVideo() {
    const urlParams = new URLSearchParams(window.location.search);
    const videoId = urlParams.get('v');

    if (videoId && videoId !== currentVideoId) {
        console.log("YT RAG Chatbot: New video detected:", videoId);
        currentVideoId = videoId;
        checkVideoStatus(videoId);
    }
}

// Start the injection process
injectUI();

// YouTube uses a dynamic page structure (SPA), so we need to monitor for navigation changes
let lastUrl = location.href; 
new MutationObserver(() => {
  const url = location.href;
  if (url !== lastUrl) {
    lastUrl = url;
    checkForVideo();
  }
}).observe(document, {subtree: true, childList: true});
