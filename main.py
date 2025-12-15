from get_papers import get_daily_papers, filter_unseen_papers, save_seen_papers
from send_to_slack import send_to_slack, get_top_papers
from create_batch_evaluation import wait_for_batch
import json
from openai import OpenAI
import os
from datetime import datetime
import time
from dotenv import load_dotenv

# Load .env file if it exists (local development)
if os.path.exists('.env'):
    load_dotenv()
    print("✓ Loaded .env file")

DW_API_KEY = os.getenv("DW_API_KEY")  
DW_BASE_URL = os.getenv("DW_BASE_URL")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")  
KEYWORDS = ["large language models", "LLM", "transformers"]
MODEL_NAME = os.getenv("MODEL_NAME")

# Team interests - hardcoded for now 
TEAM_PROFILE = {
    "focus": "The team is working on building a batched API server to offer the cheapest intelligence possible. Please give any relevant papers that would be helpful when they are designing this application.",
    "interests": [
        "Batched generative AI workloads",
        "Inference optimization and cost reduction",
        "Open source models ",
        "verification of llm answers",
        "llm as a judge"
    ],
    "avoid": [
        "Pure theoretical papers without applications",
        "Incremental benchmark improvements",
        "Papers focused on training from scratch"
    ]
}

client = OpenAI(base_url=DW_BASE_URL, api_key=DW_API_KEY) 

def create_batch_evaluation(papers):
    """Create batch requests for OpenAI that are safe for gpt-4o-mini."""

    requests = []
    for paper in papers:

        prompt = f"""

        You are curating research papers for an AI engineering team.

        TEAM PROFILE:
        Focus: {TEAM_PROFILE['focus']}

        What they care about:
        {chr(10).join(f"- {interest}" for interest in TEAM_PROFILE['interests'])}

        What to avoid:
        {chr(10).join(f"- {avoid}" for avoid in TEAM_PROFILE['avoid'])}

        Evaluate this research paper.

        TITLE:
        {paper['title']}

        ABSTRACT:
        {paper['abstract']}

        INSTRUCTIONS:
        1. relevance_score: output an integer from 0 to 10.
        2. is_relevant: true if relevance_score >= 7, else false.
        3. needs_summary: true if the abstract is more than 60 words, else false.
        4. summary: if needs_summary is true, write a 1–2 sentence summary; otherwise use null.
        5. key_insight: write exactly one sentence stating the main takeaway.

        Respond ONLY with valid JSON in this format:

        {{
        "relevance_score": 0,
        "is_relevant": false,
        "needs_summary": false,
        "summary": null,
        "key_insight": "string"
        }}
        """

        requests.append({
            "custom_id": paper['id'],
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": MODEL_NAME,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a model that must output ONLY valid JSON. No explanations. No extra text."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
        })

    return requests


def daily_run(keywords):
    """Simple daily run for the team"""
    
    # 1. Fetch papers
    print("Fetching papers...")
    papers = get_daily_papers(keywords, max_results=100)
    papers = filter_unseen_papers(papers)
    
    if not papers:
        print("No new papers today!")
        return
    
    print(f"Found {len(papers)} new papers")
    
    # 2. Create batch jsonl
    requests = create_batch_evaluation(papers)
    batch_file_path = f'batch_requests_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jsonl'

    
    # 3. Submit batch
    with open(batch_file_path, 'w') as f:
        for req in requests:
            f.write(json.dumps(req) + '\n')
    
    batch_file = client.files.create(
        file=open(batch_file_path, 'rb'),
        purpose='batch'
    )
    
    batch = client.batches.create(
        input_file_id=batch_file.id,
        endpoint="/v1/chat/completions",
        completion_window="24h"
    )
    
    print(f"Batch submitted: {batch.id}")
    
    # 4. Wait for results
    results = wait_for_batch(client, batch.id)

     # Get top 10
    top_papers = get_top_papers(results, top_n=10)
    
    # Send to Slack
    send_to_slack(top_papers, papers, SLACK_WEBHOOK_URL)
    
    # Track all papers (not just top 10)
    save_seen_papers([p['id'] for p in papers])


# Run it
daily_run(
    keywords=KEYWORDS
)