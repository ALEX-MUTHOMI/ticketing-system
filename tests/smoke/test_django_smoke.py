from django.core.management import call_command


def test_django_system_check_passes():
    call_command("check")


def test_admin_login_page_responds(client):
    response = client.get("/admin/login/")
    assert response.status_code == 200
