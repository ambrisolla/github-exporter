#!/usr/bin/env python3

import time
from   prometheus_client import start_http_server, Metric, CollectorRegistry
from   multiprocessing   import Pool
from   datetime          import datetime
from   lib.github        import Github
from   datetime          import datetime
from   argparse          import ArgumentParser

class Configurations:
    
    def __init__(self):

        arg = ArgumentParser(prog='github-exporter.py', description='Github Exporter for Prometheus'
                             )
    
        arg.add_argument(
            '--token', 
            help='Github Token', 
            required=True)
        
        arg.add_argument(
            '--http-server-port', 
            help='Port to start http-server', 
            required=True)
        
        arg.add_argument(
            '--scrape-seconds', 
            help='Consider events executed  at N seconds ago.', 
            required=True)
        
        arg.add_argument(
            '--repos', 
            help='Repositories to be scanned', 
            required=True)

        args = vars(arg.parse_args())
        
        self.token            = args['token']
        self.url              = 'https://api.github.com'
        self.http_server_port = int(args['http_server_port'])
        self.repos            = args['repos'].split(',')
        self.scrape_seconds   = int(args['scrape_seconds'])


class Collector:

    def __init__(self):

        config = Configurations()

        self.repos         = config.repos
        self.token         = config.token
        self.scrap_seconds = int(config.scrape_seconds)
        self.api_url       = 'https://api.github.com'
        self.github        = Github(token=self.token, api_url=self.api_url)
        self.pool          = Pool(16)
        self.registry      = CollectorRegistry()
        
    def collect(self):

        ''' Get Github API rate limit '''
        limits = self.github.limit()
                
        github_api_rate_limit = Metric(
            'github_api_rate_limit',
            'github_api_rate_limit', 
            'gauge')
        github_api_rate_limit.add_sample(
            'github_api_rate_limit', 
            value=limits['rate']['limit'], 
            labels={})
        yield github_api_rate_limit

        github_api_rate_used = Metric(
            'github_api_rate_used',
            'github_api_rate_used', 
            'gauge')
        github_api_rate_used.add_sample(
            'github_api_rate_used', 
            value=limits['rate']['used'], 
            labels={})
        yield github_api_rate_used
        
        github_api_rate_reset = Metric(
            'github_api_rate_reset',
            'github_api_rate_reset', 
            'gauge')
        github_api_rate_reset.add_sample(
            'github_api_rate_reset', 
            value=limits['rate']['reset'], 
            labels={})
        yield github_api_rate_reset
        
        ''' Get information about Repositories '''
        repositories = self.pool.map(
            self.github.repository, 
            self.repos)
        
        for info in repositories:

            github_repository = Metric(
                'github_repository',
                'Github repository info',
                'gauge')
            github_repository.add_sample(
                'github_repository',
                value=1,
                labels=info)
            yield github_repository

            value = 1 if info['visibility'] == 'public' else 0
            github_repository_is_public = Metric(
                'github_repository_is_public',
                'Github repository is public',
                'gauge')
            github_repository_is_public.add_sample(
                'github_repository_is_public',
                value=value,
                labels={
                    'repository': info['repository']
                })
            yield github_repository_is_public

            github_repository_open_issues_count = Metric(
                'github_repository_open_issues_count',
                'Github repository issues',
                'gauge')
            github_repository_open_issues_count.add_sample(
                'github_repository_open_issues_count',
                value=int(info['open_issues_count']),
                labels={
                    'repository': info['repository']
                })
            yield github_repository_open_issues_count

        actions_workflows_runs = self.pool.map(
            self.github.actions_workflows_runs, 
            self.repos)

        for runs in actions_workflows_runs:

            in_progress_count                        = runs['in_progress_count']
            github_actions_workflow_runs_in_progress = Metric(
                'github_actions_workflow_runs_in_progress',
                'github_actions_workflow_runs_in_progress',
                'gauge')
            github_actions_workflow_runs_in_progress.add_sample(
                'github_actions_workflow_runs_in_progress',
                value  = in_progress_count,
                labels = {
                    'repository': runs['repository']
                })
            yield github_actions_workflow_runs_in_progress

            queued_count = runs['queued_count']
            github_actions_workflow_runs_queued = Metric(
                'github_actions_workflow_runs_queued',
                'github_actions_workflow_runs_in_progress',
                'gauge')
            github_actions_workflow_runs_queued.add_sample(
                'github_actions_workflow_runs_queued',
                value  = queued_count,
                labels = {
                    'repository': runs['repository']
                })
            yield github_actions_workflow_runs_queued

            for run in runs['runs']:

                updated_at = datetime.strptime(
                    run['updated_at'],
                    '%Y-%m-%dT%H:%M:%SZ')
                
                if (datetime.utcnow() - updated_at).seconds <= self.scrap_seconds:

                    if run['status'] == 'queued':
                        status = 0
                    elif run['status'] != 'queued' and run['status'] != 'completed':
                        status = 1
                    elif run['status'] == 'completed':
                        status = 2

                    github_actions_workflow_run = Metric(
                        'github_actions_workflow_run',
                        'Github actions: workflow run details',
                        'gauge')
                    github_actions_workflow_run.add_sample(
                        'github_actions_workflow_run',
                        value  = status,
                        labels = run)
                    yield github_actions_workflow_run

                    run_started_at = datetime.strptime(
                        run['run_started_at'], 
                        '%Y-%m-%dT%H:%M:%SZ')
                    updated_at = datetime.strptime(
                        run['updated_at'], 
                        '%Y-%m-%dT%H:%M:%SZ')
                    diff_in_seconds = (updated_at-run_started_at)

                    github_actions_workflow_run_latency = Metric(
                        'github_actions_workflow_run_latency',
                        'Github Action Workflow Run latency',
                        'gauge')
                    github_actions_workflow_run_latency.add_sample(
                        'github_actions_workflow_run_latency',
                        labels=run,
                        value=diff_in_seconds.seconds)
                    yield github_actions_workflow_run_latency

        prs_all = self.pool.map(
            self.github.repository_pull_requests, self.repos)
        for prs in prs_all:
            for pr in prs['pulls']:

                if pr['state'] == 'open':
                    ''' metric: github_pull_request '''
                    github_pull_request = Metric(
                        'github_pull_request',
                        'github_pull_request',
                        'gauge')
                    github_pull_request.add_sample(
                        'github_pull_request',
                        value  = 1,
                        labels = {
                            'repository' : str(prs['repository']),
                            'html_url'   : str(pr['html_url']),
                            'number'     : str(pr['number']),
                            'locked'     : str(pr['locked']),
                            'title'      : str(pr['title']),
                            'user'       : str(pr['user']['login']),
                            'created_at' : str(pr['created_at']),
                            'updated_at' : str(pr['updated_at']),
                            'merged_at'  : str(pr['merged_at']),
                            'closed_at'  : str(pr['closed_at']),
                            'state'      : 'open'
                        })
                    yield github_pull_request
                elif pr['state'] == 'closed':
                    closed_at = datetime.strptime(
                        pr['closed_at'],
                        '%Y-%m-%dT%H:%M:%SZ')

                    if (datetime.utcnow() - closed_at).total_seconds() <= self.scrap_seconds:

                        github_pull_request = Metric(
                            'github_pull_request',
                            'github_pull_request',
                            'gauge')
                        github_pull_request.add_sample(
                            'github_pull_request',
                            value  = 0,
                            labels = {
                                'repository' : str(prs['repository']),
                                'html_url'   : str(pr['html_url']),
                                'number'     : str(pr['number']),
                                'locked'     : str(pr['locked']),
                                'title'      : str(pr['title']),
                                'user'       : str(pr['user']['login']),
                                'created_at' : str(pr['created_at']),
                                'updated_at' : str(pr['updated_at']),
                                'merged_at'  : str(pr['merged_at']),
                                'closed_at'  : str(pr['closed_at']),
                                'state'      : 'closed'
                            })
                        yield github_pull_request

if __name__ == '__main__':
    config = Configurations()
    start_http_server(
        int(config.http_server_port), 
        registry=Collector())
    while True:
        time.sleep(1)