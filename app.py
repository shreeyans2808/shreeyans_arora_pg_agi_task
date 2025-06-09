import streamlit as st
import os
from groq import Groq
import json
from datetime import datetime

# Initialize Groq client with Streamlit secrets
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

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
    
    # Then initialize messages and add greeting
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Add initial greeting message
        initial_greeting = get_chat_response("")
        st.session_state.messages.append({"role": "assistant", "content": initial_greeting})

def get_chat_response(user_input):
    # Update conversation state based on user input
    update_conversation_state(user_input)
    
    # Prepare messages for the API
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(conversation_state=st.session_state.conversation_state)},
        *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
    ]
    
    # Only add user input if it's not empty (for initial greeting)
    if user_input:
        messages.append({"role": "user", "content": user_input})
    
    # Get response from Groq
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=messages,
        temperature=0.7,
        max_tokens=1024,
    )
    
    return response.choices[0].message.content

def save_conversation_data():
    """Save the conversation data to a JSON file"""
    # Create data directory if it doesn't exist
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # Prepare the data to save
    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "candidate_info": st.session_state.conversation_state["collected_info"],
        "tech_stack": st.session_state.conversation_state["collected_info"].get("tech_stack", []),
        "scores": st.session_state.conversation_state["scores"],
        "conversation_summary": [
            {"role": msg["role"], "content": msg["content"]} 
            for msg in st.session_state.messages
        ]
    }
    
    # Generate filename with timestamp
    filename = f"data/candidate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Save to file
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    
    return filename

def update_conversation_state(user_input):
    state = st.session_state.conversation_state
    
    # Check for conversation end
    if any(word in user_input.lower() for word in ["goodbye", "bye", "exit", "quit"]):
        state["stage"] = "ending"
        # Save conversation data when ending
        filename = save_conversation_data()
        # Add a message about data being saved
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"Thank you for your time! Your interview data has been saved to {filename}"
        })
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
            state["current_tech"] = techs[0]
            state["current_question_index"] = 0
    elif state["stage"] == "technical_questions":
        current_tech = state["current_tech"]
        if current_tech in state["scores"]:
            # Update score for current question
            if "questions" not in state["scores"][current_tech]:
                state["scores"][current_tech]["questions"] = []
            
            # Move to next question or next technology
            state["current_question_index"] += 1
            if state["current_question_index"] >= len(state["questions"].get(current_tech, [])):
                # Move to next technology
                current_tech_index = state["collected_info"]["tech_stack"].index(current_tech)
                if current_tech_index + 1 < len(state["collected_info"]["tech_stack"]):
                    state["current_tech"] = state["collected_info"]["tech_stack"][current_tech_index + 1]
                    state["current_question_index"] = 0
                else:
                    state["stage"] = "summary"

def main():
    st.title("TalentScout AI Hiring Assistant")
    
    initialize_session_state()
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get and display assistant response
        with st.chat_message("assistant"):
            response = get_chat_response(prompt)
            st.write(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main() 