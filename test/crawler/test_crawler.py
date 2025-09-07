import requests

def test_create_crawl_job():
    response = requests.post("http://localhost:5002/v1/crawl/job", json={
        "urls": ["https://blog.csdn.net/2401_83794450/article/details/151158504"],
        "browser_config": {},
        "crawler_config": {}
    })
    assert response.status_code == 202
    data = response.json()
    assert "task_id" in data
    task_id = data["task_id"]
    print(task_id)

def test_query_crawl_job_status():
    task_id = "crawl_e0ae0d9e"  # Replace with a valid task_id obtained from
    # Check the status of the crawl job
    response = requests.get(f"http://localhost:5002/v1/crawl/job/{task_id}")
    assert response.status_code == 200
    status_data = response.json()
    print(status_data)

