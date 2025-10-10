"""
Example script to test R3 (Requirement Refinement)
"""
import requests
import uuid
import json
import time

# Configuration
BASE_URL = "http://localhost:8000/api/v1"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def main():
    print_section("R3 - Requirement Refinement Test")
    
    # 1. Create a project
    print("1. Creating project...")
    project_data = {
        "name": "E-commerce Platform",
        "description": "A modern e-commerce platform"
    }
    
    response = requests.post(f"{BASE_URL}/projects", json=project_data)
    if response.status_code != 200:
        print(f"Error creating project: {response.text}")
        return
    
    project = response.json()
    project_id = project["id"]
    print(f"✓ Project created: {project_id}")
    print(json.dumps(project, indent=2))
    
    # 2. Add requirements (with intentional ambiguities)
    print("\n2. Adding requirements with ambiguities...")
    
    requirements = [
        {
            "code": "REQ-001",
            "data": {
                "description": "The system should be fast and user-friendly with good performance"
            }
        },
        {
            "code": "REQ-002",
            "data": {
                "description": "The system depends on payment gateway and should handle many concurrent users"
            }
        },
        {
            "code": "REQ-003",
            "data": {
                "description": "It should probably integrate with external APIs appropriately"
            }
        }
    ]
    
    for req in requirements:
        response = requests.post(
            f"{BASE_URL}/projects/{project_id}/requirements",
            json=req
        )
        if response.status_code == 200:
            print(f"✓ Added {req['code']}")
        else:
            print(f"✗ Failed to add {req['code']}: {response.text}")
    
    # 3. Start refinement (Round 1)
    print_section("Round 1: Initial Analysis")
    
    request_id_1 = str(uuid.uuid4())
    refine_request = {
        "max_rounds": 3,
        "request_id": request_id_1
    }
    
    response = requests.post(
        f"{BASE_URL}/projects/{project_id}/refine",
        json=refine_request
    )
    
    if response.status_code == 202:
        result = response.json()
        print("✓ Refinement started (async)")
        print(json.dumps(result, indent=2))
        
        # Extract questions (in real scenario, would poll task status)
        if result.get("open_questions"):
            print("\n📋 Questions Generated:")
            for i, q in enumerate(result["open_questions"], 1):
                print(f"\n  Q{i} [{q.get('category', 'N/A').upper()}]")
                print(f"  {q.get('text', 'N/A')}")
                print(f"  Priority: {q.get('priority', 'N/A')}")
    else:
        print(f"✗ Refinement failed: {response.text}")
        return
    
    # 4. Simulate answering questions (Round 2)
    print_section("Round 2: Providing Answers")
    
    # In real scenario, questions would come from task result
    # Here we simulate with example answers
    request_id_2 = str(uuid.uuid4())
    answers = [
        {
            "question_id": "q1",
            "text": "Response time: p95 < 200ms, p99 < 500ms. UI: SUS score > 80.",
            "confidence": 5
        },
        {
            "question_id": "q2",
            "text": "Stripe API v2023-10-16. Support 1000 concurrent users.",
            "confidence": 4
        },
        {
            "question_id": "q3",
            "text": "REST APIs with OAuth 2.0. Timeout: 5s. Retry: 3x with exponential backoff.",
            "confidence": 5
        }
    ]
    
    refine_request_2 = {
        "max_rounds": 3,
        "request_id": request_id_2,
        "answers": answers
    }
    
    response = requests.post(
        f"{BASE_URL}/projects/{project_id}/refine",
        json=refine_request_2
    )
    
    if response.status_code == 202:
        result = response.json()
        print("✓ Answers submitted")
        print(json.dumps(result, indent=2))
        
        if result.get("refined_requirements_version"):
            print(f"\n✓ Requirements updated to version {result['refined_requirements_version']}")
    else:
        print(f"✗ Failed to submit answers: {response.text}")
    
    # 5. Get all QA sessions
    print_section("QA Sessions History")
    
    response = requests.get(f"{BASE_URL}/projects/{project_id}/qa-sessions")
    
    if response.status_code == 200:
        sessions = response.json()
        print(f"Total sessions: {sessions['total']}")
        
        for session in sessions.get("sessions", []):
            print(f"\n  Round {session['round']}:")
            print(f"  - Questions: {len(session.get('questions', []))}")
            print(f"  - Answers: {len(session.get('answers', [])) if session.get('answers') else 0}")
            print(f"  - Created: {session.get('created_at', 'N/A')}")
            
            if session.get('quality_flags'):
                qf = session['quality_flags']
                print(f"  - Quality Score: {qf.get('total_score', 'N/A')}")
    else:
        print(f"✗ Failed to get sessions: {response.text}")
    
    # 6. Test idempotency
    print_section("Testing Idempotency")
    
    print("Sending duplicate request_id...")
    response = requests.post(
        f"{BASE_URL}/projects/{project_id}/refine",
        json={
            "max_rounds": 3,
            "request_id": request_id_1  # Same as first request
        }
    )
    
    if response.status_code == 202:
        result = response.json()
        print("✓ Idempotency handled")
        print(json.dumps(result, indent=2))
    
    print_section("Test Complete")
    print(f"Project ID: {project_id}")
    print(f"\nView in Swagger: http://localhost:8000/docs#/qa_sessions")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to server.")
        print("  Make sure the backend is running: python main.py")
    except Exception as e:
        print(f"\n✗ Error: {e}")
