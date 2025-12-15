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
    
    # Make sure directory exists (only if there's actually a directory in the path)
    dirname = os.path.dirname(SEEN_PAPERS_FILE)
    if dirname:  # Only create directory if path includes one
        os.makedirs(dirname, exist_ok=True)
    
    with open(SEEN_PAPERS_FILE, 'w') as f:
        json.dump(list(seen), f, indent=2)
    
    print(f"✓ Tracked {len(seen)} total papers")

def filter_unseen_papers(papers):
    """Remove papers we've already sent"""
    seen = load_seen_papers()
    return [p for p in papers if p['id'] not in seen]

def get_daily_papers(keywords, max_results=100):
    """Get papers from the last 24 hours"""

    # On Mondays, look back 3 days to catch Friday's papers
    day_of_week = datetime.now().weekday()
    lookback_days = 3 if day_of_week == 0 else 1  # 0 = Monday
    
    cutoff_date = datetime.now() - timedelta(days=lookback_days)
        
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
        if paper.published.replace(tzinfo=None) >= cutoff_date:
            daily_papers.append({
                'id': paper.entry_id.split('/')[-1],
                'title': paper.title,
                'authors': [a.name for a in paper.authors],
                'abstract': paper.summary,
                'published': paper.published,
                'url': paper.entry_id
            })
    
    return daily_papers