import pytest


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200


def test_list_templates(client):
    r = client.get("/api/templates/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) >= 1


def test_get_template(client):
    r = client.get("/api/templates/business-blue")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == "business-blue"
    assert "cover" in data["slides"]


def test_generate_ppt(client):
    r = client.post("/api/ppt/generate", json={"topic": "测试主题"})
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "测试主题"
    assert len(data["slides"]) > 0


def test_get_presentation(client):
    gen = client.post("/api/ppt/generate", json={"topic": "测试"})
    pres_id = gen.json()["id"]
    r = client.get(f"/api/ppt/{pres_id}")
    assert r.status_code == 200
    assert r.json()["id"] == pres_id


def test_get_presentation_not_found(client):
    r = client.get("/api/ppt/nonexistent")
    assert r.status_code == 404


def test_get_slide(client):
    gen = client.post("/api/ppt/generate", json={"topic": "测试"})
    data = gen.json()
    r = client.get(f"/api/ppt/{data['id']}/slides/1")
    assert r.status_code == 200
    assert "html_content" in r.json()


def test_list_llm_providers(client):
    r = client.get("/api/llm/providers")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
