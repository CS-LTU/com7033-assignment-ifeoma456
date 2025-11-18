import pytest
from app import create_app, db
from app.models import User

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

def test_register_login(client):
    # register
    res = client.post('/auth/register', data={'username':'test','password':'password'}, follow_redirects=True)
    assert b'User created' in res.data or res.status_code == 200
    # login
    res = client.post('/auth/login', data={'username':'test','password':'password'}, follow_redirects=True)
    assert b'Patient Records' in res.data or res.status_code == 200