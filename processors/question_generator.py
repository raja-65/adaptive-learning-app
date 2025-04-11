import os
import uuid
from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
import json

def generate_questions(node: Dict[str, Any], num_questions: int = 3) -> List[Dict[str, Any]]:
    """
    Generate multiple-choice questions for a knowledge node using Groq LLM
    """
    # Initialize Groq LLM
    llm = Groq(
        api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama3-70b-8192"  # Using Llama 3 70B model
    )
    
    # Create a template for generating questions
    template = """
    You are an expert medical educator creating multiple-choice questions for medical students.
    
    Create {num_questions} challenging multiple-choice questions based on the following medical concept:
    
    Title: {title}
    
    Content: {content}
    
    For each question:
    1. Write a clear question that tests understanding, not just recall
    2. Provide 4 options (A, B, C, D)
    3. Indicate the correct answer (0-3, where 0=A, 1=B, 2=C, 3=D)
    4. Include a brief explanation of why the answer is correct
    
    Format your response as a JSON array of objects with the following structure:
    [
      {{
        "question": "Question text here?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_answer": 0,
        "explanation": "Explanation of why Option A is correct"
      }}
    ]
    
    Ensure your questions are medically accurate and appropriate for medical students.
    """
    
    # Create the prompt
    prompt = PromptTemplate(
        template=template,
        input_variables=["title", "content", "num_questions"]
    )
    
    # Generate the prompt
    formatted_prompt = prompt.format(
        title=node["title"],
        content=node["content"],
        num_questions=num_questions
    )
    
    # Get response from Groq
    response = llm.invoke(formatted_prompt)
    
    try:
        # Extract the JSON part from the response
        json_str = extract_json_from_response(response)
        
        # Parse the JSON
        questions = json.loads(json_str)
        
        # Add node_id to each question
        for question in questions:
            question["node_id"] = node["id"]
            question["id"] = str(uuid.uuid4())
        
        return questions
    except Exception as e:
        print(f"Error parsing response: {e}")
        print(f"Response: {response}")
        return []

def extract_json_from_response(response: str) -> str:
    """Extract JSON from the LLM response"""
    # Find the start and end of the JSON part
    start_idx = response.find('[')
    end_idx = response.rfind(']') + 1
    
    if start_idx == -1 or end_idx == 0:
        raise ValueError("No JSON found in response")
    
    return response[start_idx:end_idx]
