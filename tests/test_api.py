from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def ask(q): return client.post('/ask', json={'question': q}).json()

def test_health_and_answer():
    assert client.get('/health').json()['passages'] >= 12
    response = ask('How do I submit a medical certificate for absence?')
    assert response['status'] == 'answered'
    assert response['citations']

def test_attendance_conflict():
    response = ask('Can I sit an exam with 68% attendance?')
    assert response['status'] == 'conflict'
    assert len(response['citations']) >= 2

def test_refund_conflict():
    assert ask('What is the refund deadline?')['status'] == 'conflict'

def test_silence_is_not_a_guess():
    assert ask('Can I bring my pet parrot to lectures?')['status'] == 'not_covered'

def test_audit_exposes_evaluation_provenance():
    audit = client.get('/audit').json()
    assert audit['corpus_words'] >= 6000
    assert audit['abstention_test_questions'] == 25
    assert len(audit['planted_conflicts']) == 3

def test_conflict_can_be_handed_to_human_review():
    created = client.post('/review-cases', json={'question': 'Can I sit an exam with 68% attendance?', 'note': 'Needs formal interpretation', 'citations': []})
    assert created.status_code == 201
    case = created.json()
    assert client.patch(f"/review-cases/{case['id']}/resolve").json()['status'] == 'resolved'
