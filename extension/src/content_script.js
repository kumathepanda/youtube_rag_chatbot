// --- Constants ---
const API_BASE_URL = "https://talktotube.onrender.com";

// --- State ---
let currentVideoId = null;
let userApiKey = null; // To hold the user's API key

// --- Main Execution ---
async function injectUI() {
    try {
        const response = await fetch(chrome.runtime.getURL('src/injected_ui.html'));
        const html = await response.text();
        
        const uiContainer = document.createElement('div');
        uiContainer.innerHTML = html;
        document.body.appendChild(uiContainer);

        addEventListeners();
        makeDraggable();
        
        // Check for a saved API key before checking for a video
        checkApiKey();

    } catch (error) {
        console.error("TalkToTube: Error injecting UI:", error);
    }
}

function makeDraggable() {
    const chatContainer = document.getElementById('rag-chat-container');
    const chatHeader = document.getElementById('rag-chat-header');
    let isDragging = false;
    let offsetX, offsetY;

    chatHeader.addEventListener('mousedown', (e) => {
        isDragging = true;
        offsetX = e.clientX - chatContainer.getBoundingClientRect().left;
        offsetY = e.clientY - chatContainer.getBoundingClientRect().top;
        chatContainer.style.cursor = 'grabbing';
        document.body.style.userSelect = 'none'; 
    });

    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        const x = e.clientX - offsetX;
        const y = e.clientY - offsetY;
        chatContainer.style.left = `${x}px`;
        chatContainer.style.top = `${y}px`;
        chatContainer.style.bottom = 'auto';
        chatContainer.style.right = 'auto';
    });

    document.addEventListener('mouseup', () => {
        isDragging = false;
        chatContainer.style.cursor = 'default';
        document.body.style.userSelect = 'auto';
    });
}

// --- Event Listeners ---
function addEventListeners() {
    document.getElementById('rag-chat-toggle-btn').addEventListener('click', toggleChatWindow);
    document.getElementById('rag-process-video-btn').addEventListener('click', handleProcessVideo);
    document.getElementById('rag-chat-form').addEventListener('submit', handleSendMessage);
    // Add event listener for the new save API key button
    document.getElementById('rag-save-api-key-btn').addEventListener('click', saveApiKey);
}

// --- NEW: API Key Management ---
/**
 * Checks chrome.storage for a saved Groq API key and updates the UI accordingly.
 */
function checkApiKey() {
    chrome.storage.local.get(['groqApiKey'], function(result) {
        if (result.groqApiKey) {
            userApiKey = result.groqApiKey;
            document.getElementById('rag-api-key-view').style.display = 'none';
            document.getElementById('rag-initial-view').style.display = 'block';
            checkForVideo(); // Now that we have a key, check for a video
        } else {
            document.getElementById('rag-api-key-view').style.display = 'block';
            document.getElementById('rag-initial-view').style.display = 'none';
        }
    });
}

/**
 * Saves the user-entered API key to chrome.storage.local.
 */
function saveApiKey() {
    const apiKeyInput = document.getElementById('rag-api-key-input');
    const key = apiKeyInput.value.trim();
    if (key) {
        chrome.storage.local.set({ groqApiKey: key }, function() {
            console.log('TalkToTube: API Key saved.');
            userApiKey = key;
            document.getElementById('rag-api-key-view').style.display = 'none';
            document.getElementById('rag-initial-view').style.display = 'block';
            checkForVideo();
        });
    } else {
        document.getElementById('rag-api-key-status').textContent = "Please enter a valid key.";
    }
}

// --- UI Logic ---
function toggleChatWindow() {
    const container = document.getElementById('rag-chat-container');
    container.classList.toggle('minimized');
}

function displayMessage(text, sender) {
    const messagesContainer = document.getElementById('rag-chat-messages');
    
    const messageContainer = document.createElement('div');
    messageContainer.className = `rag-chat-message-container ${sender}`;

    if (sender === 'bot') {
        const avatar = document.createElement('div');
        avatar.className = 'bot-avatar';
        messageContainer.appendChild(avatar);
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `rag-chat-message ${sender}`;
    if (sender === 'bot') {
        messageDiv.innerHTML = marked.parse(text);
    } else {
        messageDiv.textContent = text;
    }
    
    messageContainer.appendChild(messageDiv);
    messagesContainer.appendChild(messageContainer);
    messagesContainer.scrollTop = messagesContainer.scrollHeight; // Auto-scroll
}

function showLoadingIndicator() {
    const messagesContainer = document.getElementById('rag-chat-messages');
    const initialView = document.getElementById('rag-initial-view');
    if(initialView) initialView.style.display = 'none';

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


// --- API Communication (MODIFIED) ---
async function checkVideoStatus(videoId) {
    if (!userApiKey) return updateStatusText("API Key is not set.");
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
        console.error("TalkToTube: Error checking video status:", error);
        updateStatusText("Could not connect to the server.");
    }
}

async function handleProcessVideo() {
    if (!currentVideoId || !userApiKey) return;

    const processBtn = document.getElementById('rag-process-video-btn');
    processBtn.disabled = true;
    updateStatusText("Processing video... this may take a moment.");

    try {
        const response = await fetch(`${API_BASE_URL}/process-video`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-Groq-API-Key': userApiKey // Add API key to header
            },
            body: JSON.stringify({ videoId: currentVideoId })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        
        updateStatusText("Processing complete!");
        activateChat();

    } catch (error) {
        console.error("TalkToTube: Error processing video:", error);
        updateStatusText(`Failed to process: ${error.message}`);
        processBtn.disabled = false;
    }
}

async function handleSendMessage(event) {
    event.preventDefault();
    const input = document.getElementById('rag-chat-input');
    const question = input.value.trim();

    if (!question || !currentVideoId || !userApiKey) return;

    displayMessage(question, 'user');
    input.value = '';
    showLoadingIndicator();

    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-Groq-API-Key': userApiKey // Add API key to header
            },
            body: JSON.stringify({ videoId: currentVideoId, question: question })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        hideLoadingIndicator();
        displayMessage(data.answer, 'bot');

    } catch (error) {
        console.error("TalkToTube: Error sending message:", error);
        hideLoadingIndicator();
        displayMessage(`Sorry, an error occurred: ${error.message}`, "bot");
    }
}

// --- YouTube Page Integration ---
function checkForVideo() {
    const urlParams = new URLSearchParams(window.location.search);
    const videoId = urlParams.get('v');

    if (videoId && videoId !== currentVideoId) {
        console.log("TalkToTube: New video detected:", videoId);
        currentVideoId = videoId;
        // Only check status if an API key is present.
        if (userApiKey) {
            // Reset UI for new video
            const messagesContainer = document.getElementById('rag-chat-messages');
            messagesContainer.querySelectorAll('.rag-chat-message-container, .loading').forEach(el => el.remove());
            document.getElementById('rag-initial-view').style.display = 'block';
            document.getElementById('rag-chat-input').disabled = true;
            document.getElementById('rag-chat-send-btn').disabled = true;
            updateStatusText("");

            checkVideoStatus(videoId);
        }
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