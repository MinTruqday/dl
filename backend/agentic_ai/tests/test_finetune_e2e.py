import pytest
import httpx
import time
import asyncio

@pytest.mark.asyncio
async def test_finetune_e2e_training(api_client: httpx.AsyncClient):
    user_id = "test_user_e2e_" + str(int(time.time()))
    
    # 1. Create dataset
    req_data = {
        "user_id": user_id,
        "name": "E2E Test Dataset",
        "description": "Integration testing dataset"
    }
    response = await api_client.post("/tinh-chinh/tap-du-lieu", json=req_data)
    assert response.status_code == 200
    dataset = response.json()
    dataset_id = dataset["_id"]
    
    # 2. Add samples (Need at least 10 for the job to run according to the code)
    # The `create_job` method enforces `sample_count < 10`
    samples = []
    for i in range(12):
        samples.append({
            "instruction": f"Question {i}",
            "input": "",
            "output": f"Answer {i}"
        })
        
    samples_req = {
        "user_id": user_id,
        "samples": samples
    }
    response = await api_client.post(f"/tinh-chinh/tap-du-lieu/{dataset_id}/mau-thu", json=samples_req)
    assert response.status_code == 200
    
    # 3. Create job (Using a super small model to avoid freezing)
    job_req = {
        "user_id": user_id,
        "dataset_id": dataset_id,
        "job_name": "Test E2E Training",
        "base_model": "hf-internal-testing/tiny-random-LlamaForCausalLM", 
        "method": "lora",
        "epochs": 1,
        "batch_size": 2,
        "learning_rate": 2e-4,
        "lora_rank": 8,
        "lora_alpha": 16
    }
    response = await api_client.post("/tinh-chinh/tien-trinh", json=job_req)
    assert response.status_code == 200
    job_res = response.json()
    job_id = job_res["_id"]
    
    # 4. Start job
    start_req = {"user_id": user_id}
    response = await api_client.post(f"/tinh-chinh/tien-trinh/{job_id}/bat-dau", json=start_req)
    assert response.status_code == 200
    assert response.json()["status"] == "started"
    
    # 5. Poll job status until completion
    max_retries = 60 # 60 * 5 = 300 seconds (5 minutes timeout)
    success = False
    
    for _ in range(max_retries):
        response = await api_client.get(f"/tinh-chinh/tien-trinh/{job_id}?user_id={user_id}")
        assert response.status_code == 200
        job_status = response.json()
        
        status = job_status.get("status")
        progress = job_status.get("progress", 0)
        
        print(f"Job Status: {status}, Progress: {progress}%")
        
        if status == "completed":
            success = True
            break
        if status == "failed":
            print(f"Job failed! Error: {job_status.get('error_message')}")
            break
            
        await asyncio.sleep(5)
        
    assert success is True, "Fine-tuning job did not complete successfully in time"
    
    # Verify outputs are recorded
    response = await api_client.get(f"/tinh-chinh/tien-trinh/{job_id}?user_id={user_id}")
    job_final = response.json()
    assert "merged_model_name" in job_final
    assert "adapter_path" in job_final
