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


def test_llm_status(client):
    r = client.get("/api/llm/status")
    assert r.status_code == 200
    data = r.json()
    assert "effective_provider" in data
    assert "providers" in data


def test_insert_slide(client):
    gen = client.post("/api/ppt/generate", json={"topic": "测试"})
    data = gen.json()
    pres_id = data["id"]
    n = len(data["slides"])
    blank = "<!DOCTYPE html><html><body style='width:1920px;height:1080px;margin:0'><p>插入页</p></body></html>"
    r = client.post(f"/api/ppt/{pres_id}/slides", json={"html_content": blank, "after_index": 0})
    assert r.status_code == 200
    assert r.json()["page_number"] >= 1
    assert "插入页" in r.json()["html_content"]
    full = client.get(f"/api/ppt/{pres_id}")
    assert len(full.json()["slides"]) == n + 1


def test_patch_slide_html(client):
    gen = client.post("/api/ppt/generate", json={"topic": "测试"})
    data = gen.json()
    pres_id = data["id"]
    slide = data["slides"][0]
    new_html = "<!DOCTYPE html><html><head><meta charset=\"UTF-8\"/></head><body style=\"width:1920px;height:1080px;margin:0\"><p>手动补丁</p></body></html>"
    r = client.patch(
        f"/api/ppt/{pres_id}/slide-html",
        json={"slide_id": slide["id"], "html_content": new_html},
    )
    assert r.status_code == 200
    assert "手动补丁" in r.json()["html_content"]
    page = client.get(f"/api/ppt/{pres_id}/slides/1")
    assert "手动补丁" in page.json()["html_content"]


def test_delete_slide(client):
    gen = client.post("/api/ppt/generate", json={"topic": "删除测试"})
    data = gen.json()
    pres_id = data["id"]
    assert len(data["slides"]) >= 4
    sid = data["slides"][0]["id"]
    r = client.post(f"/api/ppt/{pres_id}/delete-slide", json={"slide_id": sid})
    assert r.status_code == 200
    full = client.get(f"/api/ppt/{pres_id}")
    assert len(full.json()["slides"]) == len(data["slides"]) - 1


def test_propose_outline(client):
    r = client.post("/api/ppt/outline", json={"topic": "量子计算科普"})
    assert r.status_code == 200
    data = r.json()
    assert "steps" in data and isinstance(data["steps"], list)
    assert "outline" in data and isinstance(data["outline"], str)
