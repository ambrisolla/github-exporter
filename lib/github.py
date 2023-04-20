import sys
import requests
import json
import pytz
import urllib.parse
from datetime import datetime, timedelta


class Github:

    def __init__(self, **kwargs):
        self.token = kwargs['token']
        self.api_url = kwargs['api_url']
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

    '''
      Get repositories informations
    '''

    def limit(self):
        req = requests.get(
            f'{self.api_url}/rate_limit',
            headers=self.headers)
        if req.status_code != 200:
            print(f'Error: {str(req.reason)}\n')
            sys.exit(1)
        data = json.loads(req.text)
        return data

    def repository(self, repo):
        req = requests.get(
            f'{self.api_url}/repos/{repo}?per_page=100',
            headers=self.headers)
        data = json.loads(req.text)
        keys = ['id', 'private', 'name',
                'description', 'has_issues', 'has_discussions',
                'disabled', 'visibility', 'default_branch',
                'created_at', 'updated_at', 'pushed_at',
                'full_name', 'open_issues_count', 'archived']

        labels = {}

        for key in keys:
            labels[key] = str(data[key])
            labels['repository'] = data['full_name']

        return labels

    def repository_pull_requests(self, repo):
        req = requests.get(
            f'{self.api_url}/repos/{repo}/pulls?per_page=100&state=all',
            headers=self.headers)
        data = json.loads(req.text)
        return {
            'repository': repo,
            'pulls': data
        }

    '''
      Get Github Action Workflows runs
    '''

    def actions_workflows_runs(self, repo):
        now = datetime.now(pytz.UTC)
        created_at = (now - timedelta(seconds=120)).isoformat()

        base_url = f'{self.api_url}/repos/{repo}/actions/runs'
        params = {
            "per_page": 100
        }

        req = requests.get(
            urllib.parse.unquote(base_url),
            headers=self.headers, params=params)
        if req.ok:
            data = req.json()
            runs = data.get("workflow_runs", [])
            data = [r for r in runs if r["created_at"] > created_at]
        else:
            print(f'Error: {req.status_code}')

        runs = []
        in_progress_count = 0
        queued_count = 0

        if req.status_code == 200:
            data = json.loads(req.text)
            if data['total_count'] > 0:
                keys = [
                    'id', 'name', 'head_sha', 'path',
                    'display_title', 'event', 'run_number',
                    'status', 'conclusion', 'workflow_id',
                    'created_at', 'updated_at', 'run_started_at']

                for run in data['workflow_runs']:
                    labels = {}
                    for key in keys:
                        labels[key] = str(run[key])
                    labels['author_name'] = run['head_commit']['author']['name']
                    labels['author_email'] = run['head_commit']['author']['email']
                    labels['committer_name'] = run['head_commit']['committer']['name']
                    labels['committer_email'] = run['head_commit']['committer']['email']
                    labels['repository'] = run['repository']['full_name']
                    labels['repository_name'] = run['repository']['name']

                    runs.append(labels)

                    if run['status'] == 'in_progress':
                        in_progress_count = in_progress_count + 1
                    elif run['status'] == 'queued':
                        queued_count = queued_count + 1

            return {
                'runs': runs,
                'in_progress_count': in_progress_count,
                'queued_count': queued_count,
                'repository': repo
            }
