import streamlit as st
import openai
import os
import csv
from datetime import datetime
import uuid

# --- Configuration ---
BOOK_CONTEXT = "The Priory of the Orange Tree"
OPENAI_MODEL = "gpt-4o" # Specify your desired model
FEEDBACK_FILE = "feedback_log.csv"
CSV_HEADERS = ["timestamp", "book_context", "ai_response_id", "ai_response_text", "rating", "comment"]

# --- OpenAI API Key ---
# Ensure your OpenAI API key is set in Streamlit's secrets
# For local development, you might set it as an environment variable
# or directly: openai.api_key = "YOUR_API_KEY"
try:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
except KeyError:
    st.error("OpenAI API key not found. Please set it in Streamlit secrets (secrets.toml).")
    st.stop()

# --- CSS Styles ---
def load_css():
    st.markdown("""
    <style>
        /* Chat Bubbles */
        .message-container {
            display: flex;
            margin-bottom: 10px;
            padding: 0 5px; /* Add some padding to prevent touching edges */
        }
        .user-message-outer {
            display: flex;
            justify-content: flex-end;
            width: 100%;
        }
        .assistant-message-outer {
            display: flex;
            justify-content: flex-start;
            width: 100%;
        }
        .message-bubble {
            border-radius: 15px;
            padding: 10px 15px;
            max-width: 70%; /* Max width of bubble */
            word-wrap: break-word;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .user-message .message-bubble {
            background-color: #D0E0F0; /* Light blue */
            color: #1E1E1E;
            margin-left: auto; /* Pushes to the right */
        }
        .assistant-message .message-bubble {
            background-color: #E9E9EB; /* Grey */
            color: #1E1E1E;
            margin-right: auto; /* Pushes to the left */
        }

        /* Feedback Section */
        .feedback-section-container {
            background-color: #f8f9fa; /* Light grey background for separation */
            padding: 15px;
            border-radius: 10px;
            height: 100%; /* Make it fill the column space if possible */
        }
        .feedback-title {
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }
        .feedback-buttons-row {
            display: flex;
            justify-content: center; /* Center thumbs */
            margin-bottom: 15px;
        }
        .feedback-button {
            text-decoration: none;
            border: 2px solid transparent;
            padding: 6px 10px; /* Slightly smaller padding */
            border-radius: 8px;
            cursor: pointer;
            transition: transform 0.1s ease-in-out, border-color 0.1s ease-in-out;
            font-size: 1.5em; /* Larger emojis */
            background-color: #FFFFFF; 
            margin: 0 8px; /* Spacing between thumbs */
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            color: #333; /* Default color for emoji */
        }
        .feedback-button:hover {
            transform: scale(1.1);
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .thumb-up-selected {
            border-color: green !important;
            transform: scale(1.15) !important;
            /* color: green !important; */ /* Emoji color might not change this way, border is key */
        }
        .thumb-down-selected {
            border-color: red !important;
            transform: scale(1.15) !important;
            /* color: red !important; */
        }
        .feedback-comment textarea {
            min-height: 80px !important; /* Reduced height */
            border-radius: 8px;
        }
        .submit-feedback-button button {
            width: 100%;
            background-color: #007bff; /* Streamlit primary color */
            color: white;
            border-radius: 8px;
            padding: 10px 0;
        }
        .submit-feedback-button button:hover {
            background-color: #0056b3;
            color: white;
        }
        .feedback-submitted-message {
            text-align: center;
            color: green;
            font-weight: bold;
            padding: 20px;
            background-color: #e6ffe6;
            border-radius: 8px;
        }
    </style>
    """, unsafe_allow_html=True)

# --- Feedback Logging ---
def ensure_feedback_file_exists():
    if not os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)

def log_feedback_to_csv(book_ctx, response_id, response_text, rating, comment_text):
    ensure_feedback_file_exists()
    timestamp = datetime.now().isoformat()
    with open(FEEDBACK_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, book_ctx, response_id, response_text, rating, comment_text])

# --- Session State Initialization ---
if "openai_client" not in st.session_state:
    st.session_state.openai_client = openai.OpenAI(api_key=openai.api_key)

if "messages" not in st.session_state: # Stores all messages for display
    st.session_state.messages = []

if "latest_ai_message_id" not in st.session_state: # ID of the AI message currently eligible for feedback
    st.session_state.latest_ai_message_id = None

if "rating_for_latest_ai" not in st.session_state: # "up", "down", or None
    st.session_state.rating_for_latest_ai = None

if "comment_for_latest_ai" not in st.session_state: # Text of the comment
    st.session_state.comment_for_latest_ai = ""

if "submitted_feedback_ids" not in st.session_state: # Set of AI message IDs for which feedback has been submitted
    st.session_state.submitted_feedback_ids = set()

if "system_prompt_sent" not in st.session_state:
    st.session_state.system_prompt_sent = False
    
# --- Main App ---
st.set_page_config(page_title=f"ReadWith: {BOOK_CONTEXT}", layout="wide")
load_css()

st.title(f"Chat about: {BOOK_CONTEXT}")

# Handle query params for thumb selection
query_params = st.query_params
if "rate_msg_id" in query_params and "rating_value" in query_params:
    msg_id_from_query = query_params.get("rate_msg_id")
    rating_from_query = query_params.get("rating_value")
    
    # Only update if it's for the current latest_ai_message_id
    # and feedback hasn't been submitted for it yet
    if st.session_state.latest_ai_message_id == msg_id_from_query and \
       msg_id_from_query not in st.session_state.submitted_feedback_ids:
        st.session_state.rating_for_latest_ai = rating_from_query
    
    # Clear query params by redirecting to the page without them
    # This is important to prevent re-processing on subsequent Streamlit reruns
    # that are not due to clicking these links.
    st.query_params.clear()
    # A full rerun will happen due to query_params changing initially, then clearing them
    # and another rerun will occur. This is standard Streamlit behavior.


# Layout: Chat on left (75%), Feedback on right (25%)
chat_col, feedback_col = st.columns([0.75, 0.25])

with chat_col:
    # Display chat messages
    for msg in st.session_state.messages:
        container_class = "user-message-outer" if msg["role"] == "user" else "assistant-message-outer"
        bubble_class_prefix = "user" if msg["role"] == "user" else "assistant"
        
        st.markdown(f"""
        <div class="{container_class}">
            <div class="{bubble_class_prefix}-message">
                <div class="message-bubble">
                    {msg["content"]}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

with feedback_col:
    st.markdown("<div class='feedback-section-container'>", unsafe_allow_html=True)
    st.markdown("<div class='feedback-title'>Rate AI's Last Response</div>", unsafe_allow_html=True)

    latest_ai_msg = None
    if st.session_state.latest_ai_message_id:
        for msg_obj in reversed(st.session_state.messages): # Find the actual message object
            if msg_obj["role"] == "assistant" and msg_obj["id"] == st.session_state.latest_ai_message_id:
                latest_ai_msg = msg_obj
                break
    
    if latest_ai_msg:
        current_ai_msg_id = latest_ai_msg["id"]

        if current_ai_msg_id in st.session_state.submitted_feedback_ids:
            st.markdown("<div class='feedback-submitted-message'>Feedback Submitted!</div>", unsafe_allow_html=True)
        else:
            # Thumb buttons
            up_class = "thumb-up-selected" if st.session_state.rating_for_latest_ai == "up" else ""
            down_class = "thumb-down-selected" if st.session_state.rating_for_latest_ai == "down" else ""

            # Use unique keys for query_params for each message to avoid conflicts if not cleared perfectly
            # However, rate_msg_id should suffice.
            up_link = f"?rate_msg_id={current_ai_msg_id}&rating_value=up"
            down_link = f"?rate_msg_id={current_ai_msg_id}&rating_value=down"
            
            st.markdown(f"""
            <div class="feedback-buttons-row">
                <a href='{up_link}' class='feedback-button {up_class}' target='_self'>👍</a>
                <a href='{down_link}' class='feedback-button {down_class}' target='_self'>👎</a>
            </div>
            """, unsafe_allow_html=True)

            # Comment box
            # Use a unique key for the text_area based on the message ID to ensure it resets correctly
            # or manage its state carefully. Here, we bind to st.session_state.comment_for_latest_ai
            st.session_state.comment_for_latest_ai = st.text_area(
                "Short comment (optional):", 
                value=st.session_state.comment_for_latest_ai, 
                key=f"comment_{current_ai_msg_id}", # Key ensures widget identity
                height=100,
                placeholder="Your feedback helps us improve!"
            )
            
            # Submit Feedback button
            st.markdown("<div class='submit-feedback-button'>", unsafe_allow_html=True)
            if st.button("Submit Feedback", key=f"submit_fb_{current_ai_msg_id}"):
                if st.session_state.rating_for_latest_ai: # Rating is mandatory for submission
                    log_feedback_to_csv(
                        BOOK_CONTEXT,
                        current_ai_msg_id,
                        latest_ai_msg["content"],
                        st.session_state.rating_for_latest_ai,
                        st.session_state.comment_for_latest_ai # This is now correctly from text_area
                    )
                    st.session_state.submitted_feedback_ids.add(current_ai_msg_id)
                    # Optionally, clear rating/comment for the *next* potential feedback cycle,
                    # but new AI message arrival handles this better.
                    st.success("Feedback submitted! Thank you.")
                    st.rerun() # Rerun to show "Feedback Submitted!" message and hide controls
                else:
                    st.warning("Please select a rating (👍 or 👎) before submitting.")
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Chat with the AI to provide feedback on its responses.")
    st.markdown("</div>", unsafe_allow_html=True) # End feedback-section-container


# Chat input
user_prompt = st.chat_input("Your message...")

if user_prompt:
    # Add user message to chat display
    user_message_id = str(uuid.uuid4())
    st.session_state.messages.append({"id": user_message_id, "role": "user", "content": user_prompt})

    # Prepare messages for OpenAI API
    api_messages = []
    if not st.session_state.system_prompt_sent:
        api_messages.append({
            "role": "system",
            "content": f"You are a helpful assistant knowledgeable about the book '{BOOK_CONTEXT}'. Engage in conversation about this book. Keep your responses concise and conversational."
        })
        st.session_state.system_prompt_sent = True # Ensure it's only added once conceptually to the conversation start

    for msg in st.session_state.messages:
        api_messages.append({"role": msg["role"], "content": msg["content"]})
    
    try:
        with st.spinner("ReadWith is thinking..."):
            response = st.session_state.openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=api_messages
            )
        ai_content = response.choices[0].message.content
        ai_message_id = str(uuid.uuid4())
        
        st.session_state.messages.append({"id": ai_message_id, "role": "assistant", "content": ai_content})
        
        # New AI message arrived, set it up for feedback
        st.session_state.latest_ai_message_id = ai_message_id
        st.session_state.rating_for_latest_ai = None # Reset rating for the new message
        st.session_state.comment_for_latest_ai = "" # Reset comment for the new message
        
        # If query_params were used for a previous message's rating, they are stale now.
        # The logic at the top handles query_params based on current latest_ai_message_id.

    except Exception as e:
        st.error(f"Error communicating with OpenAI: {e}")
        # Optionally remove the user's last message if AI fails, or add an error message from AI
        # For now, user message remains, error is shown.

    st.rerun() # Rerun to display new messages and update feedback panel
