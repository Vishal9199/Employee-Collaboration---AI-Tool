from flask import Flask, request, jsonify
import requests
from textblob import TextBlob
from flask_cors import CORS
from collections import Counter

app = Flask(__name__)
CORS(app)

GITHUB_API_URL = "https://api.github.com/repos/{}/commits"

@app.route('/analyze', methods=['POST'])
def analyze_repo():
    data = request.get_json()
    repo_url = data.get('repoUrl')
    
    # Fetch and process commits, issues, and pull requests
    commits = fetch_commits_from_github(repo_url)
    issues = fetch_issues_from_github(repo_url)
    pull_requests = fetch_pull_requests_from_github(repo_url)

    sentiments = analyze_sentiments(commits)
    involvement = get_user_involvement(commits)
    
    # Calculate collaboration score
    collaboration_score = calculate_collaboration_score(commits, issues, pull_requests)

    # Dummy tone data
    tone = [40, 60, 20, 50, 30]

    return jsonify({
    'sentiment': sentiments,
    'involvement': involvement,
    'issueResponses': get_issue_responses(issues),
    'tone': tone,
    'collaborationScore': collaboration_score
})


def fetch_commits_from_github(repo_url):
    parts = repo_url.rstrip('/').split('/')
    owner, repo = parts[-2], parts[-1]

    commits_url = f'https://api.github.com/repos/{owner}/{repo}/commits'
    response = requests.get(commits_url)
    
    if response.status_code == 200:
        return response.json()
    else:
        return []

def fetch_issues_from_github(repo_url):
    parts = repo_url.rstrip('/').split('/')
    owner, repo = parts[-2], parts[-1]

    issues_url = f'https://api.github.com/repos/{owner}/{repo}/issues'
    response = requests.get(issues_url)
    
    if response.status_code == 200:
        return response.json()
    else:
        return []

def fetch_pull_requests_from_github(repo_url):
    parts = repo_url.rstrip('/').split('/')
    owner, repo = parts[-2], parts[-1]

    prs_url = f'https://api.github.com/repos/{owner}/{repo}/pulls?state=all'
    response = requests.get(prs_url)
    
    if response.status_code == 200:
        return response.json()
    else:
        return []

def analyze_sentiments(commits):
    positive, neutral, negative = 0, 0, 0
    for commit in commits:
        commit_message = commit['commit']['message']
        analysis = TextBlob(commit_message)
        if analysis.sentiment.polarity > 0:
            positive += 1
        elif analysis.sentiment.polarity == 0:
            neutral += 1
        else:
            negative += 1
    total = len(commits)
    if total == 0:
        return {'positive': 0, 'neutral': 0, 'negative': 0}
    return {
        'positive': (positive / total) * 100,
        'neutral': (neutral / total) * 100,
        'negative': (negative / total) * 100
    }

def get_user_involvement(commits):
    authors = [commit['commit']['author']['name'] for commit in commits]
    count = Counter(authors)
    labels = list(count.keys())
    data = list(count.values())
    return {
        'labels': labels,
        'data': data
    }

def get_issue_responses(issues):
    assignees = [issue['assignee']['login'] if issue['assignee'] else 'Unassigned' for issue in issues]
    count = Counter(assignees)
    labels = list(count.keys())
    data = list(count.values())
    return {
        'labels': labels,
        'data': data
    }

def calculate_collaboration_score(commits, issues, pull_requests):
    total_commits = len(commits)
    merged_pull_requests = sum(1 for pr in pull_requests if pr.get('merged_at'))
    created_issues = len(issues)
    comments = sum(len(pr.get('comments', [])) for pr in pull_requests)  # Simplified for demonstration
    unique_contributors = len(set(commit['commit']['author']['name'] for commit in commits))
    
    # Define weights for each metric
    weights = {
        'commits': 0.2,
        'pull_requests': 0.3,
        'issues': 0.2,
        'comments': 0.2,
        'contributors': 0.1
    }
    
    # Normalize and calculate score
    normalized_commits = min(total_commits / 100, 1) * weights['commits']
    normalized_pull_requests = min(merged_pull_requests / 50, 1) * weights['pull_requests']
    normalized_issues = min(created_issues / 50, 1) * weights['issues']
    normalized_comments = min(comments / 200, 1) * weights['comments']
    normalized_contributors = min(unique_contributors / 20, 1) * weights['contributors']
    
    collaboration_score = (normalized_commits + normalized_pull_requests + normalized_issues +
                           normalized_comments + normalized_contributors) * 100
    
    return min(collaboration_score, 100)  # Cap score at 100

if __name__ == '__main__':
    app.run(debug=True)
