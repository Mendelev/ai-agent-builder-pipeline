"""
Test R3 end-to-end with proper async handling
"""
import requests
import uuid
import time
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_r3_e2e():
    """Test R3 end-to-end"""
    
    print("🔍 Testing R3 End-to-End")
    print("=" * 60)
    
    # 1. Create project
    print("\n1. Creating project...")
    resp = requests.post(f"{BASE_URL}/projects", json={
        "name": "Test E-commerce",
        "description": "Test project"
    })
    assert resp.status_code in [200, 201], f"Failed to create project: {resp.status_code} - {resp.text}"
    project = resp.json()
    project_id = project["id"]
    print(f"   ✓ Project ID: {project_id}")
    print(f"   ✓ Status: {project['status']}")
    
    # Step 2: Add requirement
    print("\n2. Adding requirement to project...")
    bulk_data = {
        "requirements": [
            {
                "code": "REQ-001",
                "descricao": "O sistema deve permitir que usuários façam login com email e senha",
                "criterios_aceitacao": [
                    "Usuário deve conseguir fazer login com email válido",
                    "Sistema deve validar senha com mínimo de 8 caracteres",
                    "Deve exibir mensagem de erro para credenciais inválidas"
                ],
                "prioridade": "must"
            }
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/projects/{project_id}/requirements",
        json=bulk_data
    )
    
    print(f"Status: {response.status_code}")
    
    assert response.status_code in [200, 201], f"Failed to add requirement: {response.text}"
    
    requirements = response.json()
    print(f"Requirements added: {requirements}")
    requirement = requirements[0] if requirements else None
    assert requirement is not None, "No requirement returned"
    
    # 3. Start refinement
    print("\n3. Starting refinement...")
    request_id = str(uuid.uuid4())
    resp = requests.post(
        f"{BASE_URL}/projects/{project_id}/refine",
        json={
            "max_rounds": 3,
            "request_id": request_id
        }
    )
    
    if resp.status_code != 202:
        print(f"   ✗ Error: {resp.status_code}")
        print(f"   Response: {resp.text}")
        return
    
    refine_resp = resp.json()
    print(f"   ✓ Task enqueued: {refine_resp['audit_ref']['task_id']}")
    print(f"   ✓ Status: {refine_resp['status']}")
    
    # 4. Wait a bit for task to process
    print("\n4. Waiting for task to complete...")
    for i in range(5):
        time.sleep(1)
        print(f"   Waiting... {i+1}s")
    
    # 5. Check project status
    print("\n5. Checking project status...")
    resp = requests.get(f"{BASE_URL}/projects/{project_id}")
    if resp.status_code == 200:
        updated_project = resp.json()
        print(f"   ✓ Current status: {updated_project['status']}")
        print(f"   ✓ Requirements version: {updated_project.get('requirements_version', 'N/A')}")
    else:
        print(f"   ✗ Error getting project: {resp.text}")
    
    # 6. Get QA sessions
    print("\n6. Checking QA sessions...")
    resp = requests.get(f"{BASE_URL}/projects/{project_id}/qa-sessions")
    if resp.status_code == 200:
        sessions = resp.json()
        print(f"   ✓ Total sessions: {sessions['total']}")
        
        if sessions['total'] > 0:
            session = sessions['sessions'][0]
            print(f"   ✓ Round: {session['round']}")
            print(f"   ✓ Questions: {len(session.get('questions', []))}")
            
            if session.get('questions'):
                print(f"\n   📋 Sample questions:")
                for i, q in enumerate(session['questions'][:2], 1):
                    print(f"      {i}. [{q.get('category', 'N/A')}]")
                    print(f"         {q.get('text', 'N/A')[:70]}...")
        else:
            print(f"   ⚠ No sessions found yet")
    else:
        print(f"   ✗ Error: {resp.text}")
    
    print("\n" + "=" * 60)
    print("✓ Test completed")
    print(f"\nProject ID: {project_id}")
    print(f"Request ID: {request_id}")
    print(f"\nView at: http://localhost:8000/docs#/qa_sessions")

if __name__ == "__main__":
    try:
        test_r3_e2e()
    except AssertionError as e:
        print(f"\n✗ Assertion failed: {e}")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
