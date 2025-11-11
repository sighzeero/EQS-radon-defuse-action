#!/bin/python3

import json
import os
import requests
import subprocess
import sys

from github import Github
from repominer import filters  

from ansiblemetrics.metrics_extractor import extract_all as extract_ansible_metrics 
from toscametrics.metrics_extractor import extract_all as extract_tosca_metrics 

language = os.getenv('INPUT_LANGUAGE')

# using an access token
g = Github(os.getenv('GITHUB_TOKEN'))

repo = g.get_repo(os.getenv('GITHUB_REPOSITORY'))
files = repo.get_commit(sha=os.getenv('GITHUB_SHA')).files

for file in files:
    
    content = repo.get_contents(file.filename).decoded_content.decode()

    if language == 'ansible' and filters.is_ansible_file(file.filename):
        metrics = extract_ansible_metrics(content)
    elif language == 'tosca' and filters.is_tosca_file(file.filename, content):
        metrics = extract_tosca_metrics(content)
    else:
        print('Filter Error!')
        sys.stdout.flush()

    url = f'{os.getenv("INPUT_URL")}/predict?model_id={os.getenv("INPUT_MODEL")}'
    
    for name, value in metrics.items():
        url += f'&{name}={value}'

    headers = {"ngrok-skip-browser-warning": "true"}
    response = requests.get(url, headers=headers)

    if response.status_code and response.status_code == 200:
        response_content = json.loads(response.content.decode())
        print(file.filename, ':', response_content)
        sys.stdout.flush()
    else:
        print('Response status:', response.status_code)
        sys.stdout.flush()