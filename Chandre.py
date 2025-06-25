import streamlit as st
from PIL import Image
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
from io import BytesIO
from pydub import AudioSegment
from langchain_google_genai import ChatGoogleGenerativeAI
from gtts import gTTS
import tempfile
import os
import base64
import requests

# LangChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import LLMChain

# Gemini
import google.generativeai as genai

# Set up ffmpeg path if needed (macOS Homebrew example)
AudioSegment.converter = "/opt/homebrew/bin/ffmpeg"
AudioSegment.ffprobe = "/opt/homebrew/bin/ffprobe"

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
MainMenu {visibility: hidden;}
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

/* Input Container */
.input-container {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: white;
    border-top: 1px solid #e5e7eb;
    padding: 20px;
    box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.1);
    z-index: 1000;
}

/* Chat Input Styling */
[data-testid="stChatInput"] {
    background: white !important;
    border-radius: 25px !important;
    border: 2px solid #e5e7eb !important;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1) !important;
}

[data-testid="stChatInputTextArea"] {
    background-color: transparent !important;
    border: none !important;
    border-radius: 20px !important;
    padding: 15px 20px !important;
    font-size: 16px !important;
    color: #374151 !important;
    resize: none !important;
}

[data-testid="stChatInputSubmitButton"] {
    background: #10b981 !important;
    border: none !important;
    border-radius: 20px !important;
    width: 40px !important;
    height: 40px !important;
    color: white !important;
    box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3) !important;
}

[data-testid="stChatInputSubmitButton"]:hover {
    background: #059669 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4) !important;
    transition: all 0.2s ease !important;
}

/* Microphone Button */
.mic-button {
    background: #f59e0b;
    border: none;
    border-radius: 20px;
    width: 60px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
    font-size: 16px;
    transition: all 0.2s ease;
}

.mic-button:hover {
    background-color: #d97706;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4);
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
</style>
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

if "last_tts_index" not in st.session_state:
    st.session_state.last_tts_index = -1

# Sidebar for API Key
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

prompt_voice = ChatPromptTemplate.from_messages([
    ("system", """You are Chandre The GPT, an advanced AI assistant created to help users with various tasks. Here are your key capabilities and identity:

🌟 Identity: You are Chandre The GPT - a versatile AI assistant
🎨 Capabilities: 
- Generate high-quality images based on user prompts
- Provide helpful text responses for various queries
- Engage in natural conversations
- Assist with problem-solving and creative tasks

When users ask "who are you" or similar identity questions, introduce yourself as Chandre The GPT and explain your main capabilities - that you can generate both images and text responses to help with various tasks.

For image requests (when users mention words like "draw", "generate image", "create image", "picture", "image", "visual", "show me image", "render", "make a picture"), focus on creating high-quality visual representations.

For other queries, provide helpful, informative, and engaging text responses.but keep it short only one line unless user ask for more description. """),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{user_text}")
])

def speak(reply):
    """Generate and play TTS audio"""
    try:
        tts = gTTS(text=reply, lang='en')
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmpfile:
            tts.save(tmpfile.name)
            audio_path = tmpfile.name
        
        st.audio(audio_path, format="audio/mp3", autoplay=True)
        
        try:
            os.unlink(audio_path)
        except:
            pass
    except Exception as e:
        st.error(f"TTS Error: {str(e)}")

def process_voice_audio(audio_data):
    """Process voice audio and return text"""
    if not audio_data:
        return ""
    
    try:
        with st.spinner("🎵 Processing your voice..."):
            sound = AudioSegment.from_file(BytesIO(audio_data["bytes"]), format="webm")
            
            if len(sound) == 0:
                st.warning("Recorded audio is empty.")
                return ""
                
            wav_io = BytesIO()
            sound.export(wav_io, format="wav")
            wav_io.seek(0)

            recognizer = sr.Recognizer()
            
            with sr.AudioFile(wav_io) as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio_data_sr = recognizer.record(source)
                
            try:
                user_text = recognizer.recognize_google(audio_data_sr)
                st.success(f"✨ Recognized: '{user_text}'")
                return user_text
                
            except sr.UnknownValueError:
                st.error("😅 Could not understand the audio. Please speak clearly!")
                return ""
            except sr.RequestError as e:
                st.error(f"🚫 Speech service error: {e}")
                return ""
                
    except Exception as e:
        st.error(f"⚠️ Error processing audio: {str(e)}")
        return ""

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

# Input section
col1, col2 = st.columns([8, 2])

with col1:
    user_input = st.chat_input("💬 Type your message here...")

with col2:
    # Voice input with unique key to prevent auto-activation
    audio_data = mic_recorder(
        start_prompt="🎙️ Voice", 
        stop_prompt="⏹️ Stop", 
        key=f"mic_recorder_{len(st.session_state.messages)}",  # Dynamic key
        format="webm",
        use_container_width=True
    )

# Process text input
if user_input and not st.session_state.processing:
    # Add user message immediately
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.processing = True
    st.session_state.last_input_was_voice = False  # Mark as text input
    st.rerun()

# Process the latest message if we're in processing state
if st.session_state.processing and st.session_state.messages:
    latest_msg = st.session_state.messages[-1]
    if latest_msg["role"] == "user":
        # Generate response
        response = generate_response(latest_msg["content"])
        
        # Add assistant response
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.processing = False
        st.rerun()

# Process voice input
if audio_data and not st.session_state.processing:
    user_text = process_voice_audio(audio_data)
    if user_text:
        # Add user message immediately
        st.session_state.messages.append({"role": "user", "content": user_text})
        st.session_state.processing = True
        st.session_state.last_input_was_voice = True  # Mark as voice input
        st.rerun()

# Auto-play TTS for voice responses ONLY (only for the last message if it was triggered by voice)
if (st.session_state.messages and 
    len(st.session_state.messages) >= 2 and 
    st.session_state.messages[-1]["role"] == "assistant" and
    not st.session_state.processing and
    st.session_state.last_input_was_voice):  # Only play TTS if last input was voice
    
    current_index = len(st.session_state.messages) - 1
    if current_index > st.session_state.last_tts_index:
        assistant_msg = st.session_state.messages[-1]["content"]
        
        # Play TTS for text responses or image generation confirmations
        if isinstance(assistant_msg, str):
            speak(assistant_msg)
        elif isinstance(assistant_msg, dict) and assistant_msg.get("text"):
            speak(assistant_msg["text"])
        
        st.session_state.last_tts_index = current_index
