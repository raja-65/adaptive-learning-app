import os
import uuid
from typing import List, Dict, Any
from langchain.llms import Groq
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
import json

# Define the output schema
class KnowledgeNode(BaseModel):
    id: str = Field(description="Unique identifier for the node")
    title: str = Field(description="Title of the concept")
    content: str = Field(description="Detailed explanation of the concept")
    summary: str = Field(description="Brief summary of the concept")
    prerequisites: List[str] = Field(description="List of prerequisite concept titles")

def extract_knowledge_graph(text: str) -> List[Dict[str, Any]]:
    """
    Extract a knowledge graph from the document text using Groq LLM
    Returns a list of nodes with their connections
    """
    # Initialize Groq LLM
    llm = Groq(
        api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama3-70b-8192"  # Using Llama 3 70B model
    )
    
    # Create a parser based on the KnowledgeNode schema
    parser = PydanticOutputParser(pydantic_object=KnowledgeNode)
    
    # Create a template for extracting knowledge nodes
    template = """
    You are an expert medical educator tasked with extracting key medical concepts from educational materials.
    
    Extract the main medical concepts from the following text and organize them into a knowledge graph.
    For each concept, provide:
    1. A clear title
    2. Detailed content explaining the concept
    3. A brief summary (2-3 sentences)
    4. A list of prerequisite concepts that should be understood before learning this concept
    
    Text:
    {text}
    
    Extract up to 5 key concepts from this text. Format each concept according to this JSON schema:
    {format_instructions}
    
    Return a list of these concept objects in valid JSON format.
    """
    
    # Create the prompt
    prompt = PromptTemplate(
        template=template,
        input_variables=["text"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    # Process the text in chunks if it's too long
    max_chunk_size = 8000  # Adjust based on model's context window
    chunks = [text[i:i+max_chunk_size] for i in range(0, len(text), max_chunk_size)]
    
    all_nodes = []
    
    for chunk in chunks:
        # Generate the prompt
        formatted_prompt = prompt.format(text=chunk)
        
        # Get response from Groq
        response = llm.invoke(formatted_prompt)
        
        try:
            # Extract the JSON part from the response
            json_str = extract_json_from_response(response)
            
            # Parse the JSON
            nodes = json.loads(json_str)
            
            # Ensure each node has a unique ID
            for node in nodes:
                if not node.get('id'):
                    node['id'] = str(uuid.uuid4())
            
            all_nodes.extend(nodes)
        except Exception as e:
            print(f"Error parsing response: {e}")
            print(f"Response: {response}")
    
    # Deduplicate nodes based on title
    unique_nodes = {}
    for node in all_nodes:
        if node['title'] not in unique_nodes:
            unique_nodes[node['title']] = node
    
    return list(unique_nodes.values())

def extract_json_from_response(response: str) -> str:
    """Extract JSON from the LLM response"""
    # Find the start and end of the JSON part
    start_idx = response.find('[')
    end_idx = response.rfind(']') + 1
    
    if start_idx == -1 or end_idx == 0:
        # Try to find JSON objects if not a list
        start_idx = response.find('{')
        end_idx = response.rfind('}') + 1
        
        if start_idx == -1 or end_idx == 0:
            raise ValueError("No JSON found in response")
        
        # Wrap in array if it's a single object
        return f"[{response[start_idx:end_idx]}]"
    
    return response[start_idx:end_idx]
