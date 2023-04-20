# Github Export
Prometheus exporter for Github metrics.

## Content
- [Metrics](#metrics)
- [Configurations](#configurations)
- [Installation](#installation)
- [Docker](#docker)
- [Limitations](#limitations)
- [Dashboard](#dashboard)

## Metrics

<table>
  <tr><td><b>Name</b></td><td><b>Description</b></td><td><b>Type</b></td></tr>
  <tr><td>github_actions_workflow_run</td><td>Workflow runs for a repository</td><td>Gauge</td></tr>
  <tr><td>github_actions_workflow_run_latency</td><td>Workflow runs latency for a repository</td><td>Gauge</td></tr>
  <tr><td>github_actions_workflow_runs_in_progress</td><td>Workflow runs in progress for a repository</td><td>Gauge</td></tr>
  <tr><td>github_actions_workflow_runs_queued</td><td>Workflow runs queued for a repository</td><td>Gauge</td></tr>
  <tr><td>github_pull_request</td><td>Pull Requests for a repository</td><td>Gauge</td></tr>
  <tr><td>github_repository</td><td>Get all repositories</td><td>Gauge</td></tr>
  <tr><td>github_repository_is_public</td><td>Get repository visibility info</td><td>Gauge</td></tr>
  <tr><td>github_repository_open_issues_count</td><td>Get open issues count for a repository</td><td>Gauge</td></tr>
  <tr><td>github_api_rate_limit</td><td>Get rate limit</td><td>Gauge</td></tr>
  <tr><td>github_api_rate_reset</td><td>Get when the number of used requests will be reset. </td><td>Gauge</td></tr>
  <tr><td>github_api_rate_used</td><td>Get rate used</td><td>Gauge</td></tr>
</table>

## Usage
```bash
usage: github-exporter.py [-h] --token TOKEN \
  --http-server-port HTTP_SERVER_PORT \
  --scrape-seconds SCRAPE_SECONDS \
  --repos "userA/repo1,userA/repo2"

Github Exporter for Prometheus

options:
  -h, --help            show this help message and exit
  --token TOKEN         Github Token
  --http-server-port HTTP_SERVER_PORT
                        Port to start http-server
  --scrape-seconds SCRAPE_SECONDS
                        Consider events executed at N seconds ago.
  --repos REPOS         Repositories to be scanned
```

## Limitations
 + <b><a href="https://docs.github.com/en/rest/rate-limit?apiVersion=2022-11-28#about-rate-limits" target="_blank">Github API rate limit</a></b>: Github API has a rate limit that limits the number of requests:
   + <b>Without token</b>: 60 requests per hour
   + <b>With a personal token</b>: 5000 requests per hour
   + <b>With a enterprise token</b>: 15000 requests per hour

It means that more repositories you have set up, more request you will spend. 

## Dashboard
The dashboard below will help you analyze the metrics collected by the exporter. [ <a href="grafana/dashboard.json">JSON file</a> ]

<img src="grafana/grafana.png" />