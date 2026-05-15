"""
Comprehensive API test for TaskFlow MVP.
Run with: python test_api.py
"""
import sys, os
sys.path.insert(0, '.')
os.environ['DATABASE_URL'] = 'sqlite:///./final_test.db'
import urllib.parse

if os.path.exists('./final_test.db'):
    os.remove('./final_test.db')

from api.database import engine, Base
from api import models
Base.metadata.create_all(bind=engine)

from fastapi.testclient import TestClient
from api.main import app
client = TestClient(app)

print('=== COMPREHENSIVE API TEST ===')
print()

# ── Auth
print('--- Auth ---')
r = client.post('/auth/signup', json={'email': 'alice@test.com', 'password': 'secret123'})
assert r.status_code == 201
alice_token = r.json()['token']
alice_id = r.json()['user']['id']
print(f'Alice signup: OK (id={alice_id})')

r = client.post('/auth/signup', json={'email': 'bob@test.com', 'password': 'secret123'})
assert r.status_code == 201
bob_token = r.json()['token']
bob_id = r.json()['user']['id']
print(f'Bob signup: OK (id={bob_id})')

r = client.post('/auth/logout', headers={'Authorization': f'Bearer {alice_token}'})
assert r.status_code == 200
print('Logout: OK')

r = client.get('/auth/me', headers={'Authorization': f'Bearer {alice_token}'})
assert r.status_code == 200
print('/auth/me: OK')

# ── Teams
print()
print('--- Teams ---')
r = client.post('/teams', json={'name': 'Alpha Squad'}, headers={'Authorization': f'Bearer {alice_token}'})
assert r.status_code == 201
team = r.json()
team_id = team['id']
invite_code = team['invite_code']
print(f'Create team: OK (id={team_id}, invite_code={invite_code})')

import re
assert re.match(r'^[A-Z]{4}-[0-9]{4}$', invite_code), f'Bad invite code: {invite_code}'
print('Invite code format: OK')

r = client.post('/teams', json={'name': 'Another'}, headers={'Authorization': f'Bearer {alice_token}'})
assert r.status_code == 409
assert r.json()['error']['code'] == 'ALREADY_IN_TEAM'
print('Double-team prevention: OK')

r = client.post('/teams/join', json={'invite_code': invite_code}, headers={'Authorization': f'Bearer {bob_token}'})
assert r.status_code == 200
print('Bob join: OK')

r2 = client.post('/auth/signup', json={'email': 'eve@test.com', 'password': 'secret123'})
eve_token = r2.json()['token']
r = client.get(f'/teams/{team_id}', headers={'Authorization': f'Bearer {eve_token}'})
assert r.status_code == 403
assert r.json()['error']['code'] == 'FORBIDDEN'
print('Non-member forbidden: OK')

# ── Tasks
print()
print('--- Tasks ---')
r = client.post(f'/teams/{team_id}/tasks', json={'title': 'Fix bug #1', 'assignee_id': bob_id}, headers={'Authorization': f'Bearer {alice_token}'})
assert r.status_code == 201
t1 = r.json()
assert t1['status'] == 'TODO'
assert t1['creator_id'] == alice_id
assert t1['assignee_id'] == bob_id
print(f'Create task (assigned): OK (id={t1["id"]})')

r = client.post(f'/teams/{team_id}/tasks', json={'title': 'Write docs'}, headers={'Authorization': f'Bearer {bob_token}'})
assert r.status_code == 201
t2 = r.json()
print(f'Create task (unassigned): OK (id={t2["id"]})')

r = client.get(f'/teams/{team_id}/tasks?filter=me', headers={'Authorization': f'Bearer {alice_token}'})
assert r.status_code == 200
assert len(r.json()) == 0
print('Filter @me (alice, 0 assigned): OK')

r = client.get(f'/teams/{team_id}/tasks?filter=me', headers={'Authorization': f'Bearer {bob_token}'})
assert r.status_code == 200
assert len(r.json()) == 1
print('Filter @me (bob, 1 assigned): OK')

r = client.get(f'/teams/{team_id}/tasks?filter=unassigned', headers={'Authorization': f'Bearer {alice_token}'})
assert r.status_code == 200
assert len(r.json()) == 1
print('Filter unassigned (1): OK')

r = client.put(f'/tasks/{t1["id"]}', json={'title': 'Fix critical bug #1', 'assignee_id': alice_id}, headers={'Authorization': f'Bearer {bob_token}'})
assert r.status_code == 200
assert r.json()['title'] == 'Fix critical bug #1'
print('Update task: OK')

r = client.patch(f'/tasks/{t1["id"]}/status', json={'status': 'DOING'}, headers={'Authorization': f'Bearer {alice_token}'})
assert r.status_code == 200
assert r.json()['status'] == 'DOING'
print('Status change: OK')

r = client.delete(f'/tasks/{t1["id"]}', headers={'Authorization': f'Bearer {bob_token}'})
assert r.status_code == 403, r.text
print('Non-owner delete blocked: OK')

r = client.delete(f'/tasks/{t1["id"]}', headers={'Authorization': f'Bearer {alice_token}'})
assert r.status_code == 204
print('Creator delete: OK')

# ── Messages
print()
print('--- Messages ---')
for content in ['Hello!', 'World!', 'Foo']:
    r = client.post(f'/teams/{team_id}/messages', json={'content': content}, headers={'Authorization': f'Bearer {alice_token}'})
    assert r.status_code == 201

r = client.post(f'/teams/{team_id}/messages', json={'content': 'Bob here!'}, headers={'Authorization': f'Bearer {bob_token}'})
assert r.status_code == 201
bob_msg_id = r.json()['id']
last_msg_time = r.json()['created_at']

r = client.get(f'/teams/{team_id}/messages', headers={'Authorization': f'Bearer {alice_token}'})
assert r.status_code == 200
assert len(r.json()) == 4
print('List messages (4): OK')

since = urllib.parse.quote(last_msg_time)
r = client.get(f'/teams/{team_id}/messages?since={since}', headers={'Authorization': f'Bearer {alice_token}'})
assert r.status_code == 200
assert len(r.json()) == 0
print('Since= incremental (0 new): OK')

r = client.delete(f'/messages/{bob_msg_id}', headers={'Authorization': f'Bearer {alice_token}'})
assert r.status_code == 403
assert r.json()['error']['code'] == 'NOT_OWNER'
print('Message owner-only delete: OK')

# ── Team Management
print()
print('--- Team Management ---')

r = client.patch(f'/teams/{team_id}/transfer-owner', json={'new_owner_id': bob_id}, headers={'Authorization': f'Bearer {alice_token}'})
assert r.status_code == 200
assert r.json()['owner_id'] == bob_id
print('Transfer owner to bob: OK')

r = client.delete(f'/teams/{team_id}/leave', headers={'Authorization': f'Bearer {alice_token}'})
assert r.status_code == 204
print('Alice (member) leave: OK')

r = client.delete(f'/teams/{team_id}', headers={'Authorization': f'Bearer {bob_token}'})
assert r.status_code == 204
print('Bob (owner) delete team: OK')

r = client.get('/auth/me', headers={'Authorization': f'Bearer {bob_token}'})
assert r.json()['team_id'] is None
print('Bob team_id=NULL after deletion: OK')

print()
print('=== ALL TESTS PASSED ===')
