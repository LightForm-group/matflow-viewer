import os
import random
import time

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from matflow.api import load_workflow
from matflow.models.workflow import Workflow
from matflow.utils import get_workflow_paths, order_workflow_paths_by_date
from sqlitedict import SqliteDict
import numpy as np


from matflow_viewer import (
    app,
    GITHUB_REPO_NAME,
    DOWNLOAD_DIR,
    ALLOWED_EXTENSIONS,
    DB_PATH,
    WORKFLOW_SEARCH_DIR,
)
from matflow_viewer.formatters import (
    get_task_arguments,
    format_task_resources,
    format_parameter,
)
from matflow_viewer.utils import (
    download_file,
    get_workflow_files_from_public_repo,
)


@app.route('/')
def index():
    workflow_paths = None
    if GITHUB_REPO_NAME:
        workflow_paths = get_workflow_files_from_public_repo(GITHUB_REPO_NAME)
    else:
        if WORKFLOW_SEARCH_DIR is not None:
            local_search_path = WORKFLOW_SEARCH_DIR
        else:
            with SqliteDict(DB_PATH, autocommit=True) as dict_DB:
                local_search_path = dict_DB['workflow_search_path']
    page = render_template(
        'index.html',
        repo_name=GITHUB_REPO_NAME,
        workflow_paths=workflow_paths,
        local_search_path=local_search_path,
        search_path_editable=(WORKFLOW_SEARCH_DIR is None),
    )

    return page


@app.route('/find_local_workflows', methods=['POST', 'GET'])
def find_local_workflows():
    if request.method == 'POST':
        base_path = request.json['basePath']
        local_workflows = get_workflow_paths(base_path, quiet=False)
        # print(local_workflows)
        local_workflows = order_workflow_paths_by_date(local_workflows)[::-1]
        with SqliteDict(DB_PATH, autocommit=True) as dict_DB:
            wkflow_ids = {}
            for wk in local_workflows:
                wkflow_ids.update({wk['ID']: wk})
            dict_DB['workflow_IDs'] = wkflow_ids
            dict_DB['workflow_search_path'] = base_path

        page = render_template(
            'local_workflows.html',
            local_workflows=local_workflows,
        )
        return page
    return redirect(url_for('index'))


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
    return load_workflow(find_workflow_path(id), full_path=True)


def find_workflow_path(id):
    with SqliteDict(DB_PATH) as dict_DB:
        wk_data = dict_DB['workflow_IDs'][id]
        wk_path = wk_data['full_path']
        return wk_path


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
    wk_path = find_workflow_path(id)
    elem_data_map = Workflow.get_element_data_map(wk_path)[task_idx]
    task_parameters = [
        Workflow.get_all_element_parameters(wk_path, task_idx, elem_idx)
        for elem_idx, _ in enumerate(elem_data_map)
    ]
    schema_info = Workflow.get_schema_info(wk_path, task_idx)
    num_elements = len(elem_data_map)
    task_name = Workflow.get_task_name_friendly(wk_path, task_idx)
    tasks_info = Workflow.get_workflow_tasks_info(wk_path)
    workflow_name = 'workflow name'
    workflow_loaded_path = 'workflow loaded path'

    page = render_template(
        'workflow_tasks.html',
        id=id,
        workflow_name=workflow_name,
        workflow_loaded_path=workflow_loaded_path,
        task_idx=task_idx,
        tasks_info=tasks_info,
        task_name=task_name,
        schema_info=schema_info,
        num_elements=num_elements,
        element_idx=int(element_idx),
        active_input_name=active_input_name,
        active_output_name=active_output_name,
        active_file_name=active_file_name,
        **get_task_arguments(task_parameters),
        # resource_use=format_task_resources(task),
    )
    return page


@app.route('/workflow/<id>/figures')
@app.route('/workflow/<id>/figures/<int:figure_idx>/')
def workflow_figures(id, figure_idx=0):
    wk = find_workflow(id=id)
    fig_spec = None
    fig_JSON = None
    dat_arr_table = None
    if wk.figures:
        fig_spec = wk.figures[figure_idx]
        fig_obj = wk.get_figure_object(figure_idx, backend='plotly')
        fig_data = wk.get_figure_data(figure_idx)
        dat_arr = np.array([
            ['x'] + list(fig_data['x']),
            ['y'] + list(fig_data['y']),
        ]).T
        dat_arr_table = format_parameter(dat_arr)
        fig_JSON = fig_obj.to_json()
    page = render_template(
        'workflow_figures.html',
        id=id,
        workflow=wk,
        figure=fig_spec,
        fig_JSON=fig_JSON,
        figure_data=dat_arr_table,
    )
    return page


@app.route('/get_full_task', methods=['POST'])
def get_full_task():
    'Get task including all formatted inputs/outputs/files for all elements/iterations.'

    task_idx = int(request.form['taskIdx'])
    wid = request.form['workflowID']
    element_idx = int(request.form['elementIdx'])

    # t0 = time.perf_counter()
    # wk = find_workflow(id=wid)
    # t1 = time.perf_counter()

    # print(f'task_idx: {task_idx}')
    wk_path = find_workflow_path(wid)
    elem_data_map = Workflow.get_element_data_map(wk_path)[task_idx]
    # print(f'elem_data_map: {elem_data_map}')
    task_parameters = [
        Workflow.get_all_element_parameters(wk_path, task_idx, elem_idx)
        for elem_idx, _ in enumerate(elem_data_map)
    ]
    # print(f'task_parameters: {task_parameters}')

    # TO send:
    # - task_idx
    # - num_elements
    # - task.schema.outputs (list of str)
    # - task.schema.input_aliases (list of str)
    # - task.schema.input_map (list of dict with keys: file, inputs)
    # - task.schema.output_map (list of dict with keys: files, output)

    schema_info = Workflow.get_schema_info(wk_path, task_idx)
    num_elements = len(elem_data_map)
    task_name = Workflow.get_task_name_friendly(wk_path, task_idx)

    # task = wk.tasks[task_idx]
    page = render_template(
        'task_full.html',
        id=wid,
        task_idx=task_idx,
        task_name=task_name,
        num_elements=num_elements,
        element_idx=element_idx,
        schema_info=schema_info,
        **get_task_arguments(task_parameters),
        # resource_use=format_task_resources(task),
    )
    # t2 = time.perf_counter()

    # print(f'time to find workflow: {t1-t0:0.4f}.')
    # print(f'time to render template: {t2-t1:0.4f}.')
    return page


@app.route('/get_task_element_data/<wid>/<int:task_idx>/<int:element_idx>', methods=['GET'])
def get_task_element_data(wid, task_idx, element_idx):
    wk_path = find_workflow_path(wid)
    all_params = Workflow.get_all_element_parameters(
        wk_path,
        task_idx,
        element_idx,
        convert_numpy=True
    )
    return all_params


@app.route('/get_task_parameter_data/<wid>/<int:task_idx>', methods=['GET'])
def get_task_parameter_data(wid, task_idx):
    wk_path = find_workflow_path(wid)
    all_params = Workflow.get_task_parameter_data(wk_path, task_idx, convert_numpy=True)
    all_params = Workflow.swap_task_parameter_data_indexing(all_params)
    return jsonify(all_params)


@app.route('/get_full_figure', methods=['POST'])
def get_full_figure():
    fig_idx = int(request.form['figIdx'])
    wid = request.form['workflowID']
    wk = find_workflow(id=wid)
    fig_spec = wk.figures[fig_idx]
    fig_obj = wk.get_figure_object(fig_idx, backend='plotly')
    fig_data = wk.get_figure_data(fig_idx)
    dat_arr = np.array([
        ['x'] + list(fig_data['x']),
        ['y'] + list(fig_data['y']),
    ]).T
    dat_arr_table = format_parameter(dat_arr)
    fig_JSON = fig_obj.to_json()
    page = render_template(
        'figure_full.html',
        id=wid,
        workflow=wk,
        figure=fig_spec,
        figure_data=dat_arr_table,
        fig_JSON=fig_JSON,
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

    # print('wk: {}'.format(wk))
    # print('task: {}'.format(task))
    # print('cg_fmt: {}'.format(cg_fmt))

    page = render_template(
        'task.html',
        id=wid,
        workflow=wk,
        task=task,
        element_idx=element_idx,
        commands=cg_fmt,
    )
    return page
