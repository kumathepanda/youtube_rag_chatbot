# TalkToTube: Chat with any YouTube Video

TalkToTube is a powerful browser extension that allows you to have a conversation with any YouTube video. Using a Retrieval-Augmented Generation (RAG) pipeline, it processes the video's transcript and enables you to ask questions and get answers based exclusively on the video's content.

## ✨ Features

  * **Conversational AI**: Chat with a helpful AI assistant to understand video content quickly.
  * **Automatic Transcript Fetching**: Automatically retrieves the best available transcript for any YouTube video.
  * **Multilingual Support**: If an English transcript isn't available, it fetches a transcript in another language and translates it to English before processing.
  * **Context-Aware Answers**: The AI bases its answers **exclusively** on the information provided in the video's transcript, ensuring accuracy and relevance.
  * **Seamless YouTube Integration**: The chat interface is injected directly into the YouTube page as a draggable and minimizable widget.
  * **Powered by Modern AI Stack**: Utilizes powerful large language models via Groq for fast and intelligent responses.

-----

## 🛠️ Tech Stack

The project is divided into two main components: the backend server and the frontend Chrome extension.

  * **Backend**:

      * **Framework**: **Flask**
      * **AI/ML Orchestration**: **LangChain**
      * **LLM Provider**: **Groq** (for `Llama-3.1-8B-Instant` model)
      * **Embeddings**: **Hugging Face Transformers** (`all-MiniLM-L6-v2`)
      * **Vector Store**: **ChromaDB**
      * **Transcript API**: **youtube-transcript-api**

  * **Frontend (Chrome Extension)**:

      * **Languages**: **JavaScript, HTML, CSS**
      * **Markdown Parsing**: **Marked.js**

-----

## ⚙️ How It Works

The application follows a Retrieval-Augmented Generation (RAG) architecture:

1.  **UI Injection**: The Chrome extension injects a chat interface onto any YouTube watch page.
2.  **Video Processing**: When you click "Process Video," the extension sends the `videoId` to the Flask backend.
3.  **Transcript & Translation**: The server fetches the video's transcript. If it's not in English, it uses a Groq LLM to translate it.
4.  **Chunking & Embedding**: The transcript is split into smaller chunks, and numerical representations (embeddings) are created for each chunk using a Hugging Face model.
5.  **Vector Storage**: These embeddings are stored in a local ChromaDB vector store, indexed by the `videoId`.
6.  **Chat & Retrieval**: When you ask a question, the backend embeds your query and retrieves the most relevant chunks from the vector store.
7.  **Response Generation**: The retrieved chunks (context) and your question are passed to the `TalkTuber` AI assistant, which generates a concise answer based only on the provided information.

-----

## 🚀 Getting Started

Follow these instructions to set up and run the project locally.

### Prerequisites

  * Python 3.8+
  * Google Chrome or a Chromium-based browser

### 1\. Backend Setup

First, set up the Python server that powers the AI logic.

```bash
# 1. Clone the repository
git clone https://github.com/kumathepanda/youtube_rag_chatbot.git
cd youtube_rag_chatbot/server

# 2. Create a virtual environment and activate it
python -m venv venv
# On Windows:
# venv\Scripts\activate
# On macOS/Linux:
# source venv/bin/activate

# 3. Install the required Python packages
pip install -r requirements.txt

# 4. Set up your environment variables
#    Create a file named .env in the /server directory
#    and add your Groq API key:
echo "GROQ_API_KEY=your_groq_api_key_here" > .env

# 5. Run the Flask server
flask run
```

The server will start on `http://127.0.0.1:5000`.

### 2\. Frontend Setup

Next, load the Chrome extension.

1.  Open **Google Chrome** and navigate to `chrome://extensions`.
2.  Enable the **"Developer mode"** toggle in the top-right corner.
3.  Click the **"Load unpacked"** button.
4.  Select the `extension` folder from the cloned repository.
5.  The **TalkToTube** extension will now appear in your list of extensions and be active.

### 3\. How to Use

1.  Navigate to any video on `youtube.com`.
2.  The "Chat with Video" window will appear in the bottom-right corner.
3.  Click the **"Process Video"** button and wait for it to finish.
4.  Once processed, the chat input will become active. Ask any question about the video's content\!

-----

## 📂 Project Structure

```
.
├── extension/            # Chrome Extension source files
│   ├── icons/            # Extension icons
│   └── src/              # HTML, CSS, and JS for the extension
├── server/               # Flask backend server
│   ├── core/             # Core application logic
│   │   ├── rag_pipeline.py
│   │   └── text_preprocessing.py
│   ├── storage/          # Directory for ChromaDB vector stores
│   ├── app.py            # Main Flask application file
│   ├── config.py         # Configuration for models and paths
│   └── requirements.txt  # Python dependencies
└── README.md             # This file
```

-----

## 📄 License

This project is licensed under the MIT License.