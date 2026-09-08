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
