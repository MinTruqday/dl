import pytest
import httpx
import time

@pytest.mark.asyncio
async def test_finetune_dataset_crud(api_client: httpx.AsyncClient):
    user_id = "test_user_" + str(int(time.time()))
    
    # 1. Create dataset
    req_data = {
        "user_id": user_id,
        "name": "Test Dataset",
        "description": "A test dataset"
    }
    response = await api_client.post("/tinh-chinh/tap-du-lieu", json=req_data)
    assert response.status_code == 200
    dataset = response.json()
    assert dataset["name"] == "Test Dataset"
    assert "user_id" in dataset
    dataset_id = dataset["_id"]
    
    # 2. Add samples
    samples_req = {
        "user_id": user_id,
        "samples": [
            {"instruction": "What is AI?", "input": "", "output": "Artificial Intelligence"},
            {"instruction": "Translate to VN", "input": "Hello", "output": "Xin chào"}
        ]
    }
    response = await api_client.post(f"/tinh-chinh/tap-du-lieu/{dataset_id}/mau-thu", json=samples_req)
    assert response.status_code == 200
    add_res = response.json()
    assert add_res["added"] == 2
    
    # 3. List datasets
    response = await api_client.get(f"/tinh-chinh/tap-du-lieu?user_id={user_id}")
    assert response.status_code == 200
    datasets = response.json()
    assert len(datasets) > 0
    assert any(d["_id"] == dataset_id for d in datasets)
    
    # 4. Get specific dataset
    response = await api_client.get(f"/tinh-chinh/tap-du-lieu/{dataset_id}?user_id={user_id}")
    assert response.status_code == 200
    fetched_ds = response.json()
    assert fetched_ds["sample_count"] == 2
    
    # 5. Get samples
    response = await api_client.get(f"/tinh-chinh/tap-du-lieu/{dataset_id}/mau-thu?user_id={user_id}&limit=10")
    assert response.status_code == 200
    fetched_samples = response.json()
    assert len(fetched_samples) == 2
    
    # 6. Delete dataset
    response = await api_client.delete(f"/tinh-chinh/tap-du-lieu/{dataset_id}?user_id={user_id}")
    assert response.status_code == 200
    del_res = response.json()
    assert del_res["success"] is True
    
    # 7. Verify deletion
    response = await api_client.get(f"/tinh-chinh/tap-du-lieu/{dataset_id}?user_id={user_id}")
    assert response.status_code == 404
