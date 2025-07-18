
from flask import Flask, render_template, request, jsonify
import requests
import re
from datetime import datetime

app = Flask(__name__)

GITLAB_PROJECT_ID = '34668'
GITLAB_TRIGGER_TOKEN = ''  # Fill this in
GITLAB_TRIGGER_URL = ''    # Fill this in
GITLAB_API_URL = ''        # Fill this in
GITLAB_API_PRIVATE_TOKEN = ''  # Fill this in

@app.route('/')
def landing():
    return render_template('index.html')

@app.route('/build')
def build_form():
    return render_template('build.html')

@app.route('/submit', methods=['POST'])
def trigger_pipeline():
    data = request.form
    os_type = data.get('os')
    cuda_version = data.get('cuda_version')
    cuda = data.get('cuda')
    python_version = data.get('python_version')
    owner = data.get('owner')
    cost_center = data.get('cost_center')
    team_name = data.get('team_name')
    branch_name = re.sub(r'[^a-zA-Z0-9-_]', '-', data.get('branch_name'))

    timestamp = datetime.now().strftime('%m%d%y-%H%M%S')

    if cuda == 'true':
        ami_name = f"Amg-ASC-Cuda-{cuda_version}-{team_name}-{timestamp}"
    else:
        ami_name = f"Amg-ASC-SC-{team_name}-{timestamp}"

    instance_name = f"hpc-{cuda}-{cuda_version or 'none'}-{timestamp}"

    headers = { 'PRIVATE-TOKEN': GITLAB_API_PRIVATE_TOKEN }
    response = requests.post(f"{GITLAB_API_URL}/repository/branches", headers=headers, data={
        'branch': branch_name,
        'ref': 'main'
    })

    if response.status_code != 201:
        return jsonify({'error': 'Branch creation failed', 'details': response.json()}), 500

    response = requests.post(GITLAB_TRIGGER_URL, data={
        'token': GITLAB_TRIGGER_TOKEN,
        'ref': branch_name,
        'variables[os]': os_type,
        'variables[cuda_version]': cuda_version,
        'variables[cuda]': cuda,
        'variables[python_version]': python_version,
        'variables[ami_name]': ami_name,
        'variables[instance_name]': instance_name,
        'variables[owner]': owner,
        'variables[cost_center]': cost_center,
        'variables[team_name]': team_name
    })

    if response.status_code == 201:
        return jsonify({'message': 'AMI build triggered successfully!'}), 201
    else:
        return jsonify({'error': 'Trigger failed', 'details': response.json()}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)