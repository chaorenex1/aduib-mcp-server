from starlette.testclient import TestClient

from app import app

client = TestClient(app)

def test_crawl():
    response = client.post("/v1/crawl/job", json={
        "urls": ["https://www.bilibili.com"],
        "browser_config": {},
        "crawler_config": {}
    })
    assert response.status_code == 202
    data = response.json()
    assert "task_id" in data
    task_id = data["task_id"]

    # Check the status of the crawl job
    response = client.get(f"/v1/crawl/job/{task_id}")
    assert response.status_code == 200
    status_data = response.json()
    assert status_data["task_id"] == task_id
    assert "status" in status_data
    assert status_data["status"] in ["pending", "in_progress", "completed", "failed"]