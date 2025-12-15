# arXiv Daily Digest

**Never miss relevant research papers again.** This tool automatically fetches new papers from arXiv, evaluates them against your team's interests in batch using a LLM provided by Doubleword, and delivers a curated digest to Slack every day.

## What It Does

Every day, hundreds of papers get published on arXiv. This tool:

1. **Fetches** new papers matching your keywords
2. **Evaluates** each paper's relevance using the Doubleword Batch API
3. **Ranks** papers by how well they match your team's focus
4. **Delivers** the top 10 most relevant papers directly to Slack
5. **Tracks** what you've already seen (no duplicates)

Perfect for research teams, AI labs, or anyone who wants to stay current without drowning in papers.

## Quick Start

### Prerequisites

- Python 3.8+
- A [Doubleword API key](https://doubleword.ai) (for batch evaluations)
- A [Slack Incoming Webhook URL](https://api.slack.com/messaging/webhooks)

### Local Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/doublewordai/arxiv-daily-digest.git
   cd arxiv-daily-digest
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   
   Copy the example file:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your actual credentials:
   ```bash
   DW_API_KEY=your_actual_doubleword_api_key
   DW_BASE_URL=https://api.doubleword.ai/v1
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/ACTUAL/WEBHOOK
   MODEL_NAME=Qwen/Qwen3-VL-30B-A3B-Instruct-FP8
   ```

4. **Customize your interests**
   
   Edit `main.py` to match your team's focus:
   ```python
   KEYWORDS = ["large language models", "LLM", "transformers"]
   
   TEAM_PROFILE = {
       "focus": "Your team's research focus here",
       "interests": [
           "Topic 1",
           "Topic 2",
       ],
       "avoid": [
           "Things you don't care about",
       ]
   }
   ```

5. **Run it**
   ```bash
   python main.py
   ```

That's it! Your first digest will appear in Slack.

## How It Works

### The Pipeline

```
arXiv API → Filter New Papers → Batch Evaluation → Rank by Relevance → Slack Digest
```

**1. Paper Fetching** (`get_papers.py`)
- Searches arXiv for papers published in the last 24 hours 
- Filters by your keywords
- Removes papers you've already seen

**2. Batch Evaluation** (`main.py` + `create_batch_evaluation.py`)
- Creates evaluation requests for each paper
- Uses Doubleword's batch API for cost-efficient processing
- Scores papers 0-10 based on your team profile
- Extracts key insights and generates summaries for long abstracts
- Handles model responses with `<think>` tags if using reasoning model

**3. Slack Delivery** (`send_to_slack.py`)
- Selects only papers scoring ≥7
- Ranks by relevance score
- Formats as rich Slack blocks with links and summaries
- Sends top 10 to your given channel

### What Makes This Special

1. **Cost-Effective**: Uses batch API processing instead of real-time calls, making it significantly cheaper to evaluate hundreds of papers.
2. **Smart Filtering**: Papers are evaluated against your specific team profile, not just generic relevance.
3. **No Duplicates**: Tracks what you've seen so you never get the same paper twice.
4. **Zero Maintenance**: Set it and forget it. Run daily via cron, Docker, or Kubernetes.

## Running in Production

### Docker (Local Testing)

Build and test the container:
```bash
docker build -t arxiv-digest .
docker run --env-file .env arxiv-digest
```

### Kubernetes Deployment

1. **Build and push your image:**
   ```bash
   docker build -t your-registry/arxiv-digest:latest .
   docker push your-registry/arxiv-digest:latest
   ```

2. **Create secrets:**
   ```bash
   kubectl create secret generic arxiv-secrets \
     --from-literal=DW_API_KEY='your_actual_key' \
     --from-literal=SLACK_WEBHOOK_URL='your_actual_webhook'
     --from-literal=model_name='your_chosen_model_name' \
     --from-literal=dw_base_url='https://app.doubleword.ai/ai/v1' \
   -n daily-digest
   ```

3. **Deploy the CronJob:**
   
   Create `k8s-deployment.yaml`:
   ```yaml
   apiVersion: batch/v1
   kind: CronJob
   metadata:
     name: arxiv-digest
     namespace: daily-digest
   spec:
     schedule: "0 10 * * 1-5"  # 10 AM weekdays
     timeZone: "Europe/London"  # Adjust to your timezone
     successfulJobsHistoryLimit: 3
     failedJobsHistoryLimit: 3
     concurrencyPolicy: Forbid
     jobTemplate:
       spec:
         template:
           spec:
             restartPolicy: OnFailure
             containers:
             - name: arxiv-digest
               image: your-registry/arxiv-digest:latest
               imagePullPolicy: Always
               env:
               - name: DW_API_KEY
                 valueFrom:
                   secretKeyRef:
                     name: arxiv-secrets
                     key: dw_api_key
               - name: SLACK_WEBHOOK_URL
                 valueFrom:
                   secretKeyRef:
                     name: arxiv-secrets
                     key: slack_webhook_url
               - name: MODEL_NAME
                 valueFrom:
                   secretKeyRef:
                     name: arxiv-secrets
                     key: model_name
               - name: DW_BASE_URL
                 valueFrom:
                   secretKeyRef:
                     name: arxiv-secrets
                     key: dw_base_url
               volumeMounts:
               - name: data
                 mountPath: /app/data
               resources:
                 requests:
                   memory: "256Mi"
                   cpu: "250m"
                 limits:
                   memory: "512Mi"
                   cpu: "500m"
             volumes:
             - name: data
               persistentVolumeClaim:
                 claimName: arxiv-data-pvc
   ```

4. **Apply and verify:**
   ```bash
   kubectl apply -f k8s-deployment.yaml
   kubectl get cronjob arxiv-digest
   
   # Test manually
   kubectl create job --from=cronjob/arxiv-digest arxiv-digest-test
   kubectl logs -l job-name=arxiv-digest-test -f
   ```

### Cron Job (Traditional Server)

Run daily Mondy-Saturday at 9 AM:
```bash
0 9 * * *  cd /path/to/arxiv-daily-digest && /usr/bin/python3 main.py
```

## Configuration

### Keywords

Modify the `KEYWORDS` list in `main.py`:
```python
KEYWORDS = ["reinforcement learning", "robotics", "computer vision"]
```

### Team Profile

The `TEAM_PROFILE` tells the AI what matters to your team:

```python
TEAM_PROFILE = {
    "focus": "One sentence describing your team's work",
    "interests": [
        "Specific topics you care about",
        "Technologies you're exploring",
    ],
    "avoid": [
        "Pure theory without applications",
        "Topics outside your domain",
    ]
}
```

The more specific you are, the better the filtering.

### Scoring Threshold

By default, only papers scoring ≥7 are included. Adjust in `send_to_slack.py`:
```python
relevant = [r for r in results if r.get('is_relevant', False)]
```
## Customization Ideas

- **Change the source**: Swap arXiv for bioRxiv, medRxiv, or another preprint server
- **Multiple channels**: Send different topics to different Slack channels
- **Email digest**: Replace Slack with email delivery
- **Weekly summaries**: Aggregate top papers from the entire week
- **Custom scoring**: Modify the evaluation prompt for different criteria
- **Different models**: Change `MODEL_NAME` to experiment with other models

## Troubleshooting

**No papers found on Monday**: This is normal - arXiv doesn't publish on weekends, so the code automatically looks back 3 days to catch Friday's papers.

**Batch not completing**: Batch processing takes time. Check batch status with default 30-second intervals. For faster results during testing, adjust `check_interval` in `wait_for_batch()`.

**Slack webhook failing**: Verify your webhook URL is correct and the channel hasn't been archived.

**`seen_papers.json` corrupted**: Delete the file and it will regenerate fresh on next run.

**JSON parsing errors**: The code handles models that output `<think>` tags or extra text, but if you see persistent errors, check `create_batch_evaluation.py`'s parsing logic.

**Docker permission errors**: Ensure the `/app/data` directory has proper permissions in the container.

## Development

### Testing Locally
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Run with your .env file
python main.py
```

## Contributing

Have ideas for improvements? Found a bug? Contributions welcome!
