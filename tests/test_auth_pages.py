import pytest


@pytest.mark.django_db
def test_login_page_uses_project_template_and_css(client):
    response = client.get('/accounts/login/')

    assert response.status_code == 200
    content = response.content.decode()
    assert '/static/css/app.css' in content
    assert 'Melde dich als registrierter Recruiter an' in content
    assert 'Recruiter Login' in content


@pytest.mark.django_db
def test_signup_page_renders_without_server_error(client):
    response = client.get('/accounts/signup/')

    assert response.status_code == 200
    content = response.content.decode()
    assert '/static/css/app.css' in content
    assert 'Neues Konto' in content
    assert 'name="email"' in content


@pytest.mark.django_db
def test_password_reset_page_uses_styled_template(client):
    response = client.get('/accounts/password/reset/')

    assert response.status_code == 200
    content = response.content.decode()
    assert '/static/css/app.css' in content
    assert 'Passwort zur' in content  # covers both 'zurücksetzen' and 'zuruecksetzen'


@pytest.mark.django_db
def test_landing_uses_verified_success_state_block(client):
    response = client.get('/')

    assert response.status_code == 200
    content = response.content.decode()
    assert 'x-if="verified"' in content
    assert 'Verifiziert' in content
