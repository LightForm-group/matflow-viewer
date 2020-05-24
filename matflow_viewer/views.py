import os
import random

from flask import Flask, render_template, request, redirect, url_for, flash
from matflow.api import load_workflow

from matflow_viewer import app, GITHUB_REPO_NAME, DOWNLOAD_DIR, ALLOWED_EXTENSIONS
from matflow_viewer.formatters import get_task_arguments, format_task_resources
from matflow_viewer.utils import download_file, get_workflow_files_from_public_repo


@app.route('/')
def index():
    workflow_paths = None
    if GITHUB_REPO_NAME:
        workflow_paths = get_workflow_files_from_public_repo(GITHUB_REPO_NAME)
    tmpl = render_template(
        'index.html',
        repo_name=GITHUB_REPO_NAME,
        workflow_paths=workflow_paths
    )

    return tmpl


@app.route('/get_workflow/<path>', methods=['POST', 'GET'])
def get_remote_workflow(path):
    url = 'https://raw.githubusercontent.com/{}/master/{}'.format(GITHUB_REPO_NAME, path)
    wk_path = download_file(url)
    redirect_url = url_for('workflow_profile', id=wk_path.name)
    return redirect(redirect_url)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/get_local_workflow', methods=['GET', 'POST'])
def get_local_workflow():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            id = random.randint(0, 999)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], str(id)))
            redirect_url = url_for('workflow_profile', id=id)
            return redirect(redirect_url)

    return redirect(url_for('index'))


def find_workflow(id):
    wk_path = DOWNLOAD_DIR.joinpath(id)
    return load_workflow(wk_path, full_path=True)


@app.route('/workflow/<id>/profile')
def workflow_profile(id):
    wk = find_workflow(id=id)
    return render_template('workflow_profile.html', id=id, workflow=wk)


@app.route('/workflow/<id>/info')
def workflow_info(id):
    wk = find_workflow(id=id)
    return render_template('workflow_info.html', id=id, workflow=wk)


@app.route('/workflow/<id>/task/')
@app.route('/workflow/<id>/task/<int:task_idx>/')
@app.route('/workflow/<id>/task/<int:task_idx>/element/<element_idx>/')
@app.route('/workflow/<id>/task/<int:task_idx>/element/<element_idx>/input/<active_input_name>/')
@app.route('/workflow/<id>/task/<int:task_idx>/element/<element_idx>/output/<active_output_name>/')
@app.route('/workflow/<id>/task/<int:task_idx>/element/<element_idx>/file/<active_file_name>/')
def workflow_tasks(id, task_idx=0, element_idx=0, active_input_name=None,
                   active_output_name=None, active_file_name=None):
    wk = find_workflow(id=id)
    task = wk.tasks[task_idx]
    page = render_template(
        'workflow_tasks.html',
        id=id,
        workflow=wk,
        task=task,
        element_idx=int(element_idx),
        active_input_name=active_input_name,
        active_output_name=active_output_name,
        active_file_name=active_file_name,
        **get_task_arguments(task),
        resource_use=format_task_resources(task),
    )
    return page


@app.route('/workflow/<id>/figures')
def workflow_figures(id):
    wk = find_workflow(id=id)
    return render_template('workflow_figures.html', id=id, workflow=wk)


@app.route('/get_full_task', methods=['POST'])
def get_full_task():
    'Get task including all formatted inputs/outputs/files for all elements/iterations.'

    task_idx = int(request.form['taskIdx'])
    wid = request.form['workflowID']
    element_idx = int(request.form['elementIdx'])
    wk = find_workflow(id=wid)
    task = wk.tasks[task_idx]

    page = render_template(
        'task_full.html',
        id=wid,
        workflow=wk,
        task=task,
        element_idx=element_idx,
        **get_task_arguments(task),
        resource_use=format_task_resources(task),
    )
    return page


@app.route('/get_task', methods=['POST'])
def get_task():
    print('getting task!')
    task_idx = int(request.form['task_idx'])
    wid = request.form['wid']
    element_idx = int(request.form['element_idx'])
    wk = find_workflow(id=wid)
    task = wk.tasks[task_idx]
    cg_fmt = task.schema.command_group.get_formatted_commands([])[0]

    print('wk: {}'.format(wk))
    print('task: {}'.format(task))
    print('cg_fmt: {}'.format(cg_fmt))

    page = render_template(
        'task.html',
        id=wid,
        workflow=wk,
        task=task,
        element_idx=element_idx,
        commands=cg_fmt,
    )
    return page
