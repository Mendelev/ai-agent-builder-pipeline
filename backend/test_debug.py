import requests
import json

# Create project
response = requests.post("http://localhost:8000/api/v1/projects", json={"name": "Test Project"})
project_id = response.json()["id"]
print(f"Project created: {project_id}")

# Try bulk upsert
requirements_data = {
    "requirements": [
        {
            "code": "REQ-001",
            "descricao": "First requirement",
            "criterios_aceitacao": ["Criteria 1"],
            "prioridade": "must",
            "dependencias": []
        },
        {
            "code": "REQ-002",
            "descricao": "Second requirement",
            "criterios_aceitacao": ["Criteria 1", "Criteria 2"],
            "prioridade": "should",
            "dependencias": ["REQ-001"]
        }
    ]
}

response = requests.post(
    f"http://localhost:8000/api/v1/projects/{project_id}/requirements",
    json=requirements_data
)

print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
