import arxiv
from datetime import datetime, timedelta
import json
import os

SEEN_PAPERS_FILE = '/app/data/seen_papers.json' if os.path.exists('/app/data') else 'seen_papers.json'

def load_seen_papers():
    """Load papers we've already processed"""
    if os.path.exists(SEEN_PAPERS_FILE):
        try:
            with open(SEEN_PAPERS_FILE, 'r') as f:
                content = f.read().strip()
                if not content:
                    return set()
                return set(json.loads(content))
        except json.JSONDecodeError:
            print("Warning: seen_papers.json is corrupted, starting fresh")
            return set()
    return set()

def save_seen_papers(paper_ids):
    """Save papers we've processed"""
    seen = load_seen_papers()
    seen.update(paper_ids)
    
    # Make sure directory exists
    os.makedirs(os.path.dirname(SEEN_PAPERS_FILE), exist_ok=True)
    
    with open(SEEN_PAPERS_FILE, 'w') as f:
        json.dump(list(seen), f, indent=2)
    
    print(f"✓ Tracked {len(seen)} total papers")

def filter_unseen_papers(papers):
    """Remove papers we've already sent"""
    seen = load_seen_papers()
    return [p for p in papers if p['id'] not in seen]

def get_daily_papers(keywords, max_results=100):
    """Get papers from the last 24 hours"""
    
    yesterday = datetime.now() - timedelta(days=1)
    
    # Build search query
    query = " OR ".join([f'"{keyword}"' for keyword in keywords])
    
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending
    )
    
    client = arxiv.Client()
    daily_papers = []
    
    for paper in client.results(search):
        if paper.published.replace(tzinfo=None) >= yesterday:
            daily_papers.append({
                'id': paper.entry_id.split('/')[-1],
                'title': paper.title,
                'authors': [a.name for a in paper.authors],
                'abstract': paper.summary,
                'published': paper.published,
                'url': paper.entry_id
            })
    
    return daily_papers