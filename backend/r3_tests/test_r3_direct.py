"""
Simple test to debug R3 task execution
"""
import uuid
import time
from app.core.database import SessionLocal
from app.models.project import Project, Requirement
from app.tasks.analyst import refine_requirements

def test_r3_task():
    """Test R3 task directly"""
    db = SessionLocal()
    
    try:
        # Create project
        project = Project(
            id=uuid.uuid4(),
            name="Test Project",
            status="DRAFT"
        )
        db.add(project)
        
        # Add requirement
        requirement = Requirement(
            id=uuid.uuid4(),
            project_id=project.id,
            code="REQ-001",
            version=1,
            data={"description": "The system should be fast and user-friendly"}
        )
        db.add(requirement)
        db.commit()
        
        print(f"✓ Created project: {project.id}")
        print(f"✓ Added requirement: {requirement.code}")
        
        # Call task directly (synchronous for debugging)
        request_id = str(uuid.uuid4())
        print(f"\n🔄 Calling refine_requirements task...")
        print(f"   project_id: {project.id}")
        print(f"   request_id: {request_id}")
        
        result = refine_requirements(
            project_id=str(project.id),
            max_rounds=3,
            request_id=request_id,
            answers=None
        )
        
        print(f"\n✓ Task completed!")
        print(f"   Status: {result['status']}")
        print(f"   Round: {result['current_round']}")
        print(f"   Questions: {len(result.get('open_questions', []))}")
        
        if result.get('open_questions'):
            print(f"\n📋 Questions generated:")
            for i, q in enumerate(result['open_questions'][:3], 1):
                print(f"   {i}. [{q['category']}] {q['text'][:80]}...")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    test_r3_task()
