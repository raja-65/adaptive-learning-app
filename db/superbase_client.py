import os
from typing import List, Dict, Any
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_supabase_client() -> Client:
    """Get a Supabase client instance"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_KEY environment variables must be set"
        )

    return create_client(url, key)


def store_nodes(nodes: List[Dict[str, Any]], file_id: str, user_id: str) -> None:
    """Store knowledge nodes in Supabase"""
    supabase = get_supabase_client()

    for node in nodes:
        # Prepare node data
        node_data = {
            "id": node["id"],
            "title": node["title"],
            "content": node["content"],
            "summary": node["summary"],
            "source_file_id": file_id,
            "created_by": user_id,
            "is_ai_generated": True,
            "status": "pending",  # Needs professor approval
        }

        # Insert node
        supabase.table("study_nodes").insert(node_data).execute()

        # Store prerequisites as edges
        for prereq_title in node.get("prerequisites", []):
            # Find the prerequisite node by title
            prereq_response = (
                supabase.table("study_nodes")
                .select("id")
                .eq("title", prereq_title)
                .execute()
            )

            if prereq_response.data:
                prereq_id = prereq_response.data[0]["id"]

                # Create edge
                edge_data = {
                    "from_node_id": prereq_id,
                    "to_node_id": node["id"],
                    "relationship_type": "prerequisite",
                }

                supabase.table("node_edges").insert(edge_data).execute()


def store_questions(questions: List[Dict[str, Any]]) -> None:
    """Store questions in Supabase"""
    supabase = get_supabase_client()

    for question in questions:
        # Prepare question data
        question_data = {
            "id": question["id"],
            "node_id": question["node_id"],
            "question": question["question"],
            "options": question["options"],
            "correct_answer": question["correct_answer"],
            "explanation": question["explanation"],
        }

        # Insert question
        supabase.table("quiz_questions").insert(question_data).execute()


def update_file_status(file_id: str, status: str, message: str = None) -> None:
    """Update the status of a file in Supabase"""
    supabase = get_supabase_client()

    update_data = {"status": status}
    if message:
        update_data["error_message" if status == "error" else "message"] = message

    supabase.table("files").update(update_data).eq("id", file_id).execute()
