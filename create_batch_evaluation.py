from openai import OpenAI
import json
import time
import re

def check_batch_status(client, batch_id):
    """Check if batch is complete"""
    batch = client.batches.retrieve(batch_id)
    print(f"Status: {batch.status}")
    print(f"Completed: {batch.request_counts.completed}/{batch.request_counts.total}")
    return batch

def parse_evaluation_result(content):
    """Extract JSON from response that might have <think> tags or other text"""
    
    # Remove <think> tags if present
    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
    
    # Find JSON in the content
    content = content.strip()
    
    # If it starts with {, try to parse directly
    if content.startswith('{'):
        try:
            return json.loads(content)
        except:
            pass
    
    # Otherwise, find JSON block
    json_match = re.search(r'\{[\s\S]*\}', content)
    if json_match:
        try:
            return json.loads(json_match.group())
        except:
            pass
    
    return None


def get_batch_results(client, batch_id):
    """Retrieve and parse batch results"""
    
    batch = client.batches.retrieve(batch_id)
    
    if batch.status != "completed":
        print(f"Batch not ready. Status: {batch.status}")
        return None
    
    result_file_id = batch.output_file_id
    result = client.files.content(result_file_id)
    
    results = []
    lines = result.text.strip().split('\n')
    
    for i, line in enumerate(lines):
        try:
            data = json.loads(line)
            paper_id = data['custom_id']
            content = data['response']['body']['choices'][0]['message']['content']
            
            # Parse the evaluation JSON from content
            evaluation = parse_evaluation_result(content)
            
            if evaluation:
                evaluation['paper_id'] = paper_id
                results.append(evaluation)
                print(f"✓ Parsed {paper_id}: score={evaluation.get('relevance_score')}")
            else:
                print(f"✗ Failed to parse JSON for {paper_id}")
                
        except Exception as e:
            print(f"✗ Error on line {i}: {e}")
    
    return results

def wait_for_batch(client, batch_id, check_interval=30):
    """Wait for batch to complete"""
    
    print("Waiting for batch to complete...")
    while True:
        batch = check_batch_status(client, batch_id)
        
        if batch.status == "completed":
            print("✓ Batch completed!")
            return get_batch_results(client, batch_id)
        elif batch.status == "failed":
            print("✗ Batch failed")
            return None
        
        time.sleep(check_interval)
