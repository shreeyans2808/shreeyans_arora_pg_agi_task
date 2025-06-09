# TalentScout AI Hiring Assistant

An intelligent chatbot designed to assist in the initial screening of candidates for technology positions. The chatbot uses the Groq API to provide natural language interactions and generate relevant technical questions based on candidates' tech stacks.

## Features

- Professional greeting and conversation flow
- Collection of essential candidate information
- Tech stack assessment
- Dynamic technical question generation
- Context-aware conversations
- Clean and intuitive Streamlit interface
- Automated scoring system
- Conversation data persistence

## Conversation Flow and State Management

The chatbot maintains a structured conversation flow through different stages:

### 1. Greeting Stage
- Automatically initiates with a welcome message
- Explains the purpose of the conversation
- Transitions to information collection

### 2. Information Collection Stage
Collects essential candidate details in sequence:
- Full Name
- Email Address
- Phone Number
- Years of Experience
- Desired Position
- Current Location

### 3. Tech Stack Stage
- Prompts for technology expertise
- Accepts comma-separated list of technologies
- Initializes scoring system for each technology

### 4. Technical Questions Stage
For each technology, the system:
- Asks 3-5 relevant technical questions
- Questions are presented one at a time
- Maintains order of questions
- Scores answers:
  - Full correct answer = 1 mark
  - Partial correct answer = 0.5 marks
  - Incorrect or "I don't know" = 0 marks
- Provides explanations for incorrect answers
- Tracks scores per technology

### 5. Summary Stage
- Provides overall assessment
- Shows scores by technology
- Offers feedback on performance

### 6. Ending Stage
- Gracefully concludes the conversation
- Saves all collected data to a JSON file
- Provides confirmation of data storage

## Conversation State Structure

The chatbot maintains state through the following structure:
```python
conversation_state = {
    "stage": "greeting",  # Current conversation stage
    "collected_info": {},  # Candidate information
    "tech_stack": [],     # List of technologies
    "questions_asked": 0,  # Question counter
    "current_tech": None,  # Current technology being questioned
    "current_question_index": 0,  # Current question index
    "scores": {},         # Scores per technology
    "questions": {}       # Questions per technology
}
```

## Data Persistence

When the conversation ends, all data is saved to a JSON file in the `data` directory:
- Timestamp of the conversation
- Complete candidate information
- Tech stack assessment
- Scores for each technology
- Full conversation transcript

## Setup

1. Clone this repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory and add your Groq API key:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```

## Running the Application

To start the application, run:
```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501` by default.

## Usage

1. Open the application in your web browser
2. The chatbot will automatically greet you
3. Follow the prompts to provide your information
4. Answer technical questions in the order they are asked
5. End the conversation by saying "goodbye" or "exit"

## Note

Make sure to keep your Groq API key secure and never commit it to version control. 