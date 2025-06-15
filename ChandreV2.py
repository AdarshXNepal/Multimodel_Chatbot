import streamlit as st
from PIL import Image
import requests
import tempfile
import os
import base64
import json

# LangChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI

# Gemini
import google.generativeai as genai

# Page config
st.set_page_config(page_title="Chandre The GPT", page_icon="🌟", layout="wide")

# Modern Chat UI Styling
st.markdown("""
<style>
/* Global Styles */
.stApp {
    background-color: #f7f7f8;
}

/* Hide Streamlit default elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Custom Title Styling */
.chat-title {
    text-align: center;
    font-size: 2.5rem;
    font-weight: 700;
    color: #10b981;
    margin-bottom: 2rem;
    padding: 1rem 0;
    text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    position: sticky;
    top: 0;
    background: #f7f7f8;
    z-index: 100;
}

.user-message {
    display: flex;
    justify-content: flex-end;
    align-items: flex-start;
    margin: 0.5rem 0;
    width: 100%;
}

.assistant-message {
    display: flex;
    justify-content: flex-start;
    align-items: flex-start;
    margin: 0.5rem 0;
    width: 100%;
}

.user-content {
    background: #10b981;
    color: white;
    padding: 12px 18px;
    border-radius: 18px 18px 4px 18px;
    max-width: 70%;
    word-wrap: break-word;
    font-size: 0.95rem;
    line-height: 1.4;
    box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
}

.assistant-content {
    background: white;
    color: #374151;
    padding: 12px 18px;
    border-radius: 18px 18px 18px 4px;
    max-width: 70%;
    word-wrap: break-word;
    font-size: 0.95rem;
    line-height: 1.4;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    border: 1px solid #e5e7eb;
}

.message-icon {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    font-weight: bold;
    margin: 0 8px;
    flex-shrink: 0;
}

.user-icon {
    background: #10b981;
    color: white;
}

.assistant-icon {
    background: #10b981;
    color: white;
}

/* Chat Container */
.chat-container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    height: 60vh;
    overflow-y: auto;
}

/* Voice Controls */
.voice-controls {
    display: flex;
    gap: 10px;
    margin: 10px 0;
    justify-content: center;
    align-items: center;
}

.voice-button {
    background: #f59e0b;
    border: none;
    border-radius: 20px;
    padding: 10px 20px;
    color: white;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
    font-size: 14px;
    transition: all 0.2s ease;
}

.voice-button:hover {
    background-color: #d97706;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4);
}

.voice-button:disabled {
    background-color: #9ca3af;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
}

.recording {
    background: #ef4444 !important;
    animation: pulse 1s infinite;
}

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.7; }
    100% { opacity: 1; }
}

/* Add space at bottom for fixed input */
.main-content {
    padding-bottom: 150px;
}

/* Scrollbar styling */
.chat-container::-webkit-scrollbar {
    width: 6px;
}

.chat-container::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 10px;
}

.chat-container::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 10px;
}

.chat-container::-webkit-scrollbar-thumb:hover {
    background: #a8a8a8;
}

.thinking-indicator {
    background: white;
    color: #6b7280;
    padding: 12px 18px;
    border-radius: 18px 18px 18px 4px;
    max-width: 70%;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    border: 1px solid #e5e7eb;
    font-style: italic;
}

.status-message {
    text-align: center;
    padding: 10px;
    margin: 10px 0;
    border-radius: 10px;
    font-size: 14px;
}

.status-success {
    background-color: #d1fae5;
    color: #065f46;
    border: 1px solid #a7f3d0;
}

.status-error {
    background-color: #fee2e2;
    color: #991b1b;
    border: 1px solid #fca5a5;
}

.status-info {
    background-color: #dbeafe;
    color: #1e40af;
    border: 1px solid #93c5fd;
}
</style>

<!-- Web Speech API Integration -->
<script>
let recognition;
let isRecording = false;
let audioContext;
let mediaRecorder;
let audioChunks = [];

// Initialize Speech Recognition
if ('webkitSpeechRecognition' in window) {
    recognition = new webkitSpeechRecognition();
} else if ('SpeechRecognition' in window) {
    recognition = new SpeechRecognition();
}

if (recognition) {
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';
    
    recognition.onstart = function() {
        window.parent.postMessage({type: 'speech_start'}, '*');
    };
    
    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        window.parent.postMessage({type: 'speech_result', transcript: transcript}, '*');
    };
    
    recognition.onerror = function(event) {
        window.parent.postMessage({type: 'speech_error', error: event.error}, '*');
    };
    
    recognition.onend = function() {
        window.parent.postMessage({type: 'speech_end'}, '*');
    };
}

// Voice input functions
function startRecording() {
    if (recognition && !isRecording) {
        try {
            recognition.start();
            isRecording = true;
            return true;
        } catch (error) {
            console.error('Recognition start error:', error);
            return false;
        }
    }
    return false;
}

function stopRecording() {
    if (recognition && isRecording) {
        recognition.stop();
        isRecording = false;
        return true;
    }
    return false;
}

// Text-to-Speech function
function speakText(text) {
    if ('speechSynthesis' in window) {
        // Cancel any ongoing speech
        window.speechSynthesis.cancel();
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.9;
        utterance.pitch = 1;
        utterance.volume = 1;
        
        // Try to use a good voice
        const voices = window.speechSynthesis.getVoices();
        const preferredVoice = voices.find(voice => 
            voice.lang.startsWith('en') && 
            (voice.name.includes('Google') || voice.name.includes('Microsoft'))
        );
        
        if (preferredVoice) {
            utterance.voice = preferredVoice;
        }
        
        utterance.onstart = function() {
            window.parent.postMessage({type: 'tts_start'}, '*');
        };
        
        utterance.onend = function() {
            window.parent.postMessage({type: 'tts_end'}, '*');
        };
        
        utterance.onerror = function(event) {
            window.parent.postMessage({type: 'tts_error', error: event.error}, '*');
        };
        
        window.speechSynthesis.speak(utterance);
        return true;
    }
    return false;
}

// Listen for messages from parent
window.addEventListener('message', function(event) {
    if (event.data.type === 'start_recording') {
        startRecording();
    } else if (event.data.type === 'stop_recording') {
        stopRecording();
    } else if (event.data.type === 'speak_text') {
        speakText(event.data.text);
    } else if (event.data.type === 'stop_speaking') {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
        }
    }
});

// Ensure voices are loaded
if ('speechSynthesis' in window) {
    window.speechSynthesis.onvoiceschanged = function() {
        window.parent.postMessage({type: 'voices_loaded'}, '*');
    };
}
</script>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "memory" not in st.session_state:
    st.session_state.memory = ConversationBufferMemory(return_messages=True)

if "processing" not in st.session_state:
    st.session_state.processing = False

if "api_key" not in st.session_state:
    st.session_state.api_key = ""

if "last_input_was_voice" not in st.session_state:
    st.session_state.last_input_was_voice = False

if "recording" not in st.session_state:
    st.session_state.recording = False

if "voice_result" not in st.session_state:
    st.session_state.voice_result = ""

if "tts_enabled" not in st.session_state:
    st.session_state.tts_enabled = True

# Sidebar for API Key and Settings
with st.sidebar:
    st.header("🔑 API Configuration")
    api_key_input = st.text_input(
        "Enter your Gemini API Key:",
        placeholder="AIzaSy...",
        type="password",
        value=st.session_state.api_key
    )
    
    if api_key_input != st.session_state.api_key:
        st.session_state.api_key = api_key_input
        if api_key_input:
            genai.configure(api_key=api_key_input)
            st.success("✅ API Key configured!")
        else:
            st.warning("⚠️ Please enter your Gemini API key to start chatting")
    
    st.header("🎵 Voice Settings")
    st.session_state.tts_enabled = st.checkbox("Enable Text-to-Speech", value=st.session_state.tts_enabled)
    
    if st.button("🔇 Stop Speaking"):
        st.components.v1.html("""
        <script>
        parent.postMessage({type: 'stop_speaking'}, '*');
        </script>
        """, height=0)

# Header
st.markdown('<h1 class="chat-title">🎓 Chandre The GPT</h1>', unsafe_allow_html=True)

# Chat prompts
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are Chandre The GPT, an advanced AI assistant created to help users with various tasks. Here are your key capabilities and identity:

🌟 Identity: You are Chandre The GPT - a versatile AI assistant
🎨 Capabilities: 
- Generate high-quality images based on user prompts
- Provide helpful text responses for various queries
- Engage in natural conversations
- Assist with problem-solving and creative tasks

When users ask "who are you" or similar identity questions, introduce yourself as Chandre The GPT and explain your main capabilities - that you can generate both images and text responses to help with various tasks.

For image requests (when users mention words like "draw", "generate image", "create image", "picture", "image", "visual", "show me image", "render", "make a picture"), focus on creating high-quality visual representations.

For other queries, provide helpful, informative, and engaging text responses but keep it short only one line unless user ask for more description."""),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{user_input}")
])

def generate_response(user_input, is_voice=False):
    """Generate response for user input"""
    if not st.session_state.api_key:
        return "⚠️ Please input a correct Gemini API key in the sidebar to start chatting!"
    
    try:
        # Check if it's an image generation request
        image_keywords = ["draw", "generate image", "create image", "picture", "image", "visual", "show me image", "render", "make a picture"]
        if any(keyword in user_input.lower() for keyword in image_keywords):
            return generate_image(user_input)
        else:
            return generate_text_response(user_input)
            
    except Exception as e:
        return f"❌ Error: {str(e)}"

def generate_image(user_input):
    """Generate image using Gemini API"""
    try:
        IMAGE_GENERATION_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key={st.session_state.api_key}"
        
        image_generation_prompt = f"You are an image generator who generates images based on user requests. Reform their request and try bringing the best photo with best styles. User input: {user_input}"
        
        payload = {
            "instances": {
                "prompt": image_generation_prompt
            },
            "parameters": {
                "sampleCount": 1
            }
        }
        
        response = requests.post(IMAGE_GENERATION_API_URL, json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("predictions") and len(result["predictions"]) > 0 and result["predictions"][0].get("bytesBase64Encoded"):
            base64_encoded_string = result["predictions"][0]["bytesBase64Encoded"]
            image_data_uri = f"data:image/png;base64,{base64_encoded_string}"
            return {"text": "Here's the image I generated for you! ✨", "image_url": image_data_uri}
        else:
            return {"text": "❌ Error: No image data found in the API response.", "image_url": None}
            
    except Exception as e:
        return {"text": f"❌ Error generating image: {str(e)}", "image_url": None}

def generate_text_response(user_input):
    """Generate text response using LangChain"""
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=st.session_state.api_key)
        
        chain = LLMChain(
            llm=llm,
            prompt=prompt,
            memory=st.session_state.memory
        )
        
        result = chain.invoke({"user_input": user_input})
        return result["text"]
        
    except Exception as e:
        return f"❌ Error generating response: {str(e)}"

# Display chat messages
st.markdown('<div class="main-content">', unsafe_allow_html=True)

for i, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        # User message
        st.markdown(f'''
        <div class="user-message">
            <div class="user-content">{msg["content"]}</div>
            <div class="message-icon user-icon">👤</div>
        </div>
        ''', unsafe_allow_html=True)
    else:
        # Assistant message
        st.markdown(f'''
        <div class="assistant-message">
            <div class="message-icon assistant-icon">🤖</div>
        ''', unsafe_allow_html=True)
        
        if isinstance(msg["content"], str):
            st.markdown(f'''
                <div class="assistant-content">{msg["content"]}</div>
            </div>
            ''', unsafe_allow_html=True)
        elif isinstance(msg["content"], dict):
            if msg["content"].get("text"):
                st.markdown(f'''
                    <div class="assistant-content">{msg["content"]["text"]}</div>
                ''', unsafe_allow_html=True)
            if msg["content"].get("image_url"):
                st.image(msg["content"]["image_url"], width=400)
            st.markdown('</div>', unsafe_allow_html=True)

# Show thinking indicator if processing
if st.session_state.processing:
    st.markdown(f'''
    <div class="assistant-message">
        <div class="message-icon assistant-icon">🤖</div>
        <div class="thinking-indicator">Thinking... 🤔</div>
    </div>
    ''', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Voice Controls
st.markdown('<div class="voice-controls">', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if st.button("🎙️ Start Recording", disabled=st.session_state.recording or st.session_state.processing):
        st.session_state.recording = True
        st.components.v1.html("""
        <script>
        parent.postMessage({type: 'start_recording'}, '*');
        </script>
        """, height=0)
        st.rerun()

with col2:
    if st.button("⏹️ Stop Recording", disabled=not st.session_state.recording):
        st.session_state.recording = False
        st.components.v1.html("""
        <script>
        parent.postMessage({type: 'stop_recording'}, '*');
        </script>
        """, height=0)
        st.rerun()

with col3:
    if st.session_state.recording:
        st.markdown('<div class="status-message status-info">🔴 Recording... Speak now!</div>', unsafe_allow_html=True)
    elif st.session_state.processing:
        st.markdown('<div class="status-message status-info">⏳ Processing...</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Text input
user_input = st.chat_input("💬 Type your message here...")

# Process text input
if user_input and not st.session_state.processing:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.processing = True
    st.session_state.last_input_was_voice = False
    st.rerun()

# Process the latest message if we're in processing state
if st.session_state.processing and st.session_state.messages:
    latest_msg = st.session_state.messages[-1]
    if latest_msg["role"] == "user":
        response = generate_response(latest_msg["content"])
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.processing = False
        
        # Auto-play TTS for voice responses
        if st.session_state.last_input_was_voice and st.session_state.tts_enabled:
            text_to_speak = ""
            if isinstance(response, str):
                text_to_speak = response
            elif isinstance(response, dict) and response.get("text"):
                text_to_speak = response["text"]
            
            if text_to_speak:
                st.components.v1.html(f"""
                <script>
                parent.postMessage({{type: 'speak_text', text: {json.dumps(text_to_speak)}}}, '*');
                </script>
                """, height=0)
        
        st.rerun()

# Handle voice input results via JavaScript messages
voice_result_placeholder = st.empty()

# JavaScript message handler
st.components.v1.html("""
<script>
window.addEventListener('message', function(event) {
    if (event.data.type === 'speech_result') {
        // Send the transcript back to Streamlit
        const transcript = event.data.transcript;
        window.parent.postMessage({
            type: 'streamlit_set_component_value',
            value: transcript,
            dataType: 'json'
        }, '*');
    } else if (event.data.type === 'speech_error') {
        console.error('Speech recognition error:', event.data.error);
        window.parent.postMessage({
            type: 'streamlit_set_component_value',
            value: 'ERROR:' + event.data.error,
            dataType: 'json'
        }, '*');
    } else if (event.data.type === 'speech_end') {
        window.parent.postMessage({
            type: 'streamlit_set_component_value',
            value: 'ENDED',
            dataType: 'json'
        }, '*');
    }
});
</script>
""", height=0, key="voice_handler")

# Check for voice input results
if st.session_state.get("voice_result") and st.session_state.voice_result.strip():
    if st.session_state.voice_result.startswith("ERROR:"):
        st.error(f"Voice recognition error: {st.session_state.voice_result[6:]}")
    elif st.session_state.voice_result == "ENDED":
        st.session_state.recording = False
    else:
        # Process voice input
        if not st.session_state.processing:
            st.session_state.messages.append({"role": "user", "content": st.session_state.voice_result})
            st.session_state.processing = True
            st.session_state.last_input_was_voice = True
            st.success(f"✨ Recognized: '{st.session_state.voice_result}'")
    
    # Clear the result
    st.session_state.voice_result = ""
    st.rerun()

# Instructions
with st.expander("📋 How to Use Voice Features"):
    st.markdown("""
    **Voice Input:**
    - Click "🎙️ Start Recording" to begin voice input
    - Speak clearly into your microphone
    - Click "⏹️ Stop Recording" when finished
    - Your speech will be converted to text and processed
    
    **Text-to-Speech:**
    - Toggle "Enable Text-to-Speech" in the sidebar
    - When enabled, responses to voice inputs will be spoken aloud
    - Use "🔇 Stop Speaking" to interrupt TTS playback
    
    **Note:** Voice features require microphone access and work best in modern browsers like Chrome, Firefox, or Edge.
    """)

# Browser compatibility check
st.components.v1.html("""
<script>
// Check for Web Speech API support
if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    const warning = document.createElement('div');
    warning.style.cssText = 'background:#fee2e2;color:#991b1b;padding:10px;margin:10px 0;border-radius:5px;border:1px solid #fca5a5;text-align:center;';
    warning.innerHTML = '⚠️ Voice input not supported in this browser. Please use Chrome, Firefox, or Edge for voice features.';
    document.body.insertBefore(warning, document.body.firstChild);
}

if (!('speechSynthesis' in window)) {
    const warning = document.createElement('div');
    warning.style.cssText = 'background:#fee2e2;color:#991b1b;padding:10px;margin:10px 0;border-radius:5px;border:1px solid #fca5a5;text-align:center;';
    warning.innerHTML = '⚠️ Text-to-speech not supported in this browser. Please use a modern browser for voice output.';
    document.body.insertBefore(warning, document.body.firstChild);
}
</script>
""", height=0)
