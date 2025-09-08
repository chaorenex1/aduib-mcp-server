import requests

def test_create_crawl_job():
    response = requests.post("http://localhost:5002/v1/crawl/job", json={
        "urls": ["https://blog.csdn.net/weixin_33879932/article/details/114086842"],
        "browser_config": {},
        "crawler_config": {}
    })
    assert response.status_code == 202
    data = response.json()
    assert "task_id" in data
    task_id = data["task_id"]
    print(task_id)


def test_create_crawl_stream_job():
    response = requests.post("http://localhost:5002/v1/crawl/stream/job", json={
        "urls": ["https://blog.csdn.net/weixin_33879932/article/details/114086842"],
        "browser_config": {},
        "crawler_config": {}
    })
    assert response.status_code == 200
    data = response.content
    print(data)

def test_query_crawl_job_status():
    task_id = "crawl_9925e757"  # Replace with a valid task_id obtained from
    # Check the status of the crawl job
    response = requests.get(f"http://localhost:5002/v1/crawl/job/{task_id}")
    assert response.status_code == 200
    status_data = response.json()
    print(status_data)

