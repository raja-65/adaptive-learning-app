import os
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def test_groq_connection():
    """Test connection to Groq API"""
    try:
        # Simple completion request
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful medical AI assistant."},
                {"role": "user", "content": "Explain the cardiac cycle in 2 sentences."}
            ],
            max_tokens=100
        )
        
        print("Groq API connection successful!")
        print(f"Response: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"Error connecting to Groq API: {e}")
        return False

if __name__ == "__main__":
    test_groq_connection()
