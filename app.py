import streamlit as st
import os
import json
from datetime import datetime
from groq import Groq

# Initialize Groq client
@st.cache_resource
def init_groq_client():
    try:
        # Try to get API key from secrets first, then from environment
        api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
        if not api_key:
            st.error("""
            Please set your GROQ_API_KEY in your Streamlit secrets:
            
            1. For local development:
               - Create a .streamlit/secrets.toml file with:
               ```toml
               GROQ_API_KEY = "your_groq_api_key_here"
               ```
            
            2. For deployment:
               - Streamlit Cloud: Add the secret in the dashboard
               - Other platforms: Set GROQ_API_KEY environment variable
            """)
            st.stop()
        return Groq(api_key=api_key)
    except Exception as e:
        st.error(f"Error initializing Groq client: {str(e)}")
        st.stop()

# System prompt for the chatbot
SYSTEM_PROMPT = """You are an AI hiring assistant for TalentScout, a technology recruitment agency. Your role is to:
1. Greet candidates professionally
2. Collect essential information (name, email, phone, experience, desired position, location)
3. Gather their tech stack details
4. Generate relevant technical questions based on their tech stack
5. Maintain conversation context
6. End the conversation gracefully when appropriate

Guidelines:
- Be professional and friendly
- Ask one question at a time
- Validate information when provided
- Generate 3-5 technical questions per technology mentioned
- End conversation when user says goodbye, exit, or similar
- Keep responses concise and focused

Technical Question Rules:
1. Questions will be asked one at a time
2. Answers must be provided in the order questions were asked
3. For each question:
   - Full correct answer = 1 mark
   - Partial correct answer = 0.5 marks
   - Incorrect or "I don't know" = 0 marks
4. If a candidate doesn't know an answer:
   - Provide the correct answer
   - Explain the concept briefly
   - Move to the next question
5. Keep track of scores for each technology
6. At the end, provide a summary of scores by technology

Current conversation state: {conversation_state}"""

def initialize_session_state():
    # Initialize conversation state first
    if "conversation_state" not in st.session_state:
        st.session_state.conversation_state = {
            "stage": "greeting",
            "collected_info": {},
            "tech_stack": [],
            "questions_asked": 0,
            "current_tech": None,
            "current_question_index": 0,
            "scores": {},  # Format: {"tech": {"total": 0, "questions": []}}
            "questions": {}  # Format: {"tech": ["question1", "question2", ...]}
        }
    
    # Initialize session ID if not exists
    if "session_id" not in st.session_state:
        st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Initialize messages list first
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Add initial greeting only if messages is empty
    if len(st.session_state.messages) == 0:
        try:
            initial_greeting = get_chat_response("")
            if initial_greeting:
                st.session_state.messages.append({"role": "assistant", "content": initial_greeting})
        except Exception as e:
            # Fallback greeting if API call fails
            fallback_greeting = "Hello! Welcome to TalentScout AI Hiring Assistant. I'm here to help assess your technical skills. Let's start by getting to know you better. Could you please tell me your full name?"
            st.session_state.messages.append({"role": "assistant", "content": fallback_greeting})

def get_chat_response(user_input):
    try:
        client = init_groq_client()
        
        # Update conversation state based on user input
        if user_input:  # Only update if user_input is not empty
            update_conversation_state(user_input)
        
        # Prepare messages for the API
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT.format(conversation_state=st.session_state.conversation_state)},
        ]
        
        # Add conversation history (limit to last 10 messages to avoid token limits)
        recent_messages = st.session_state.messages[-10:] if len(st.session_state.messages) > 10 else st.session_state.messages
        for msg in recent_messages:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Only add user input if it's not empty (for initial greeting)
        if user_input:
            messages.append({"role": "user", "content": user_input})
        
        # Get response from Groq with error handling
        response = client.chat.completions.create(
            model="llama-3.1-70b-versatile",  # Using a more stable model
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        st.error(f"Error getting chat response: {str(e)}")
        return "I apologize, but I'm experiencing technical difficulties. Please try again in a moment."

def save_conversation_data():
    """Save the conversation data to a JSON file in memory (for display purposes)"""
    try:
        # Prepare the data to save
        data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "candidate_info": st.session_state.conversation_state.get("collected_info", {}),
            "tech_stack": st.session_state.conversation_state.get("collected_info", {}).get("tech_stack", []),
            "scores": st.session_state.conversation_state.get("scores", {}),
            "conversation_summary": [
                {"role": msg["role"], "content": msg["content"]} 
                for msg in st.session_state.messages
            ]
        }
        
        # Generate filename with timestamp and session ID
        session_id = st.session_state.get("session_id", datetime.now().strftime("%Y%m%d_%H%M%S"))
        filename = f"candidate_{session_id}.json"
        
        # Store in session state for download (since we can't write files in Streamlit Cloud)
        st.session_state.conversation_data = data
        st.session_state.conversation_filename = filename
        
        return filename
    except Exception as e:
        st.error(f"Error preparing conversation data: {str(e)}")
        return None

def update_conversation_state(user_input):
    try:
        state = st.session_state.conversation_state
        
        # Check for conversation end
        if any(word in user_input.lower() for word in ["goodbye", "bye", "exit", "quit", "thank you"]):
            state["stage"] = "ending"
            # Save conversation data when ending
            filename = save_conversation_data()
            return
        
        # Update state based on current stage
        if state["stage"] == "greeting":
            state["stage"] = "collecting_info"
        elif state["stage"] == "collecting_info":
            # Extract information based on the last question asked
            if "name" not in state["collected_info"]:
                state["collected_info"]["name"] = user_input
            elif "email" not in state["collected_info"]:
                state["collected_info"]["email"] = user_input
            elif "phone" not in state["collected_info"]:
                state["collected_info"]["phone"] = user_input
            elif "experience" not in state["collected_info"]:
                state["collected_info"]["experience"] = user_input
            elif "position" not in state["collected_info"]:
                state["collected_info"]["position"] = user_input
            elif "location" not in state["collected_info"]:
                state["collected_info"]["location"] = user_input
                state["stage"] = "tech_stack"
        elif state["stage"] == "tech_stack":
            if "tech_stack" not in state["collected_info"]:
                techs = [tech.strip() for tech in user_input.split(",")]
                state["collected_info"]["tech_stack"] = techs
                # Initialize scores for each technology
                for tech in techs:
                    state["scores"][tech] = {"total": 0, "questions": []}
                state["stage"] = "technical_questions"
                if techs:  # Check if techs list is not empty
                    state["current_tech"] = techs[0]
                    state["current_question_index"] = 0
        elif state["stage"] == "technical_questions":
            current_tech = state.get("current_tech")
            if current_tech and current_tech in state["scores"]:
                # Update score for current question
                if "questions" not in state["scores"][current_tech]:
                    state["scores"][current_tech]["questions"] = []
                
                # Move to next question or next technology
                state["current_question_index"] += 1
                tech_stack = state["collected_info"].get("tech_stack", [])
                current_questions = state["questions"].get(current_tech, [])
                
                if state["current_question_index"] >= len(current_questions):
                    # Move to next technology
                    if current_tech in tech_stack:
                        current_tech_index = tech_stack.index(current_tech)
                        if current_tech_index + 1 < len(tech_stack):
                            state["current_tech"] = tech_stack[current_tech_index + 1]
                            state["current_question_index"] = 0
                        else:
                            state["stage"] = "summary"
    except Exception as e:
        st.error(f"Error updating conversation state: {str(e)}")

def main():
    st.set_page_config(
        page_title="TalentScout AI Hiring Assistant",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    st.title("🤖 TalentScout AI Hiring Assistant")
    
    # Add a small description
    st.markdown("""
    Welcome to the TalentScout AI Hiring Assistant. I'll help assess your technical skills and experience.
    Please follow the prompts and answer the questions to the best of your ability.
    """)
    
    # Initialize session state
    initialize_session_state()
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Add download button if conversation data exists
    if hasattr(st.session_state, 'conversation_data') and st.session_state.conversation_data:
        st.sidebar.markdown("### Download Interview Data")
        st.sidebar.download_button(
            label="Download Interview JSON",
            data=json.dumps(st.session_state.conversation_data, indent=2),
            file_name=st.session_state.conversation_filename,
            mime="application/json"
        )
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = get_chat_response(prompt)
                st.write(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()