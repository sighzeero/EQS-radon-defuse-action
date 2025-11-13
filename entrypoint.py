#!/bin/python3

import json
import os
import requests
import sys
from github import Github
from repominer import filters
from ansiblemetrics.metrics_extractor import extract_all as extract_ansible_metrics
from toscametrics.metrics_extractor import extract_all as extract_tosca_metrics

language = os.getenv('INPUT_LANGUAGE')
g = Github(os.getenv('GITHUB_TOKEN'))
repo = g.get_repo(os.getenv('GITHUB_REPOSITORY'))
files = repo.get_commit(sha=os.getenv('GITHUB_SHA')).files

for file in files:
    content = repo.get_contents(file.filename, ref=os.getenv('GITHUB_SHA')).decoded_content.decode()

    metrics = {}

    try:
        if language == 'ansible':
            metrics = extract_ansible_metrics(content)
        elif language == 'tosca':
            metrics = extract_tosca_metrics(content)
        else:
            print('Filter Error! Skipping', file.filename)
            sys.stdout.flush()
            continue
    except Exception as e:
        print(f"⚠️ Errore di parsing in {file.filename}: {e}")
        sys.stdout.flush()
        metrics = {"syntax_error": 1}

    url = f'{os.getenv("INPUT_URL")}/predict?model_id={os.getenv("INPUT_MODEL")}'
    for name, value in metrics.items():
        url += f'&{name}={value}'

    headers = {"ngrok-skip-browser-warning": "true"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            response_content = json.loads(response.content.decode())
            print(file.filename, ':', response_content)
        else:
            print('Response status:', response.status_code)
    except Exception as e:
        print(f"Errore durante la richiesta al modello: {e}")

    sys.stdout.flush()
