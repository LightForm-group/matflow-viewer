import os
import random
import threading
import webbrowser
import requests
from pathlib import Path
import json
from pprint import pprint, pformat
from datetime import datetime, timedelta
import copy

import numpy as np
from hpcflow.utils import format_time_delta

from github import Github
import jinja2_highlight
from matflow.api import load_workflow
from werkzeug.utils import secure_filename

from flask import Flask, render_template, request, redirect, url_for, flash


DOWNLOAD_DIR = Path(__file__).parent.joinpath('downloaded')
GITHUB_REPO_NAME = None  # 'aplowman/matflow-workflows'
GH_TOKEN = '9c538cfd05411306582851f73a4c914d13635904'
ALLOWED_EXTENSIONS = {'hdf5'}


class MyFlask(Flask):
    jinja_options = dict(Flask.jinja_options)
    jinja_options.setdefault('extensions',
                             []).append('jinja2_highlight.HighlightExtension')


app = MyFlask(__name__)
app.config['UPLOAD_FOLDER'] = DOWNLOAD_DIR


def get_workflow_files_from_public_repo(repo_name):

    g = Github(GH_TOKEN)
    repo = g.get_repo(repo_name)
    contents = repo.get_contents('')
    workflow_paths = []
    while contents:
        file_content = contents.pop(0)
        if file_content.type == 'dir':
            contents.extend(repo.get_contents(file_content.path))
        elif file_content.path.endswith('workflow.hdf5'):
            workflow_paths.append(file_content.path)

    return workflow_paths


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
    return load_workflow(wk_path, viewer=True, full_path=True)


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


def format_task_resources(task):
    res_use = []
    for i in task.resource_usage:

        i = copy.deepcopy(i)
        # dt_fmt = r'%Y.%m.%d %H:%M:%S'
        td = timedelta(**i['duration'])
        i['duration'] = format_time_delta(td)

        res_use.append(i)

    return res_use


@app.route('/workflow/<id>/figures')
def workflow_figures(id):
    wk = find_workflow(id=id)
    return render_template('workflow_figures.html', id=id, workflow=wk)


def get_task_arguments(task):
    cg_fmt = task.schema.command_group.get_formatted_commands([])[0]
    formatted_parameters = {
        'inputs': {},
        'outputs': {},
        'files': {},
    }
    for input_elem in task.inputs:
        for input_name, input_val in input_elem.items():
            if input_name.startswith('__file__'):
                input_name = input_name.split('__file__')[1]
                if input_name not in formatted_parameters['files']:
                    formatted_parameters['files'][input_name] = []
                formatted_parameters['files'][input_name].append({
                    'url_name': input_name.replace('.', '_'),
                    'value': input_val,
                })
            else:
                if input_name not in formatted_parameters['inputs']:
                    formatted_parameters['inputs'][input_name] = []
                formatted_parameters['inputs'][input_name].append(
                    format_parameter(input_val))

    for output_elem in task.outputs:
        for output_name, output_val in output_elem.items():
            if output_name.startswith('__file__'):
                output_name = output_name.split('__file__')[1]
                if output_name not in formatted_parameters['files']:
                    formatted_parameters['files'][output_name] = []
                formatted_parameters['files'][output_name].append({
                    'url_name': output_name.replace('.', '_'),
                    'value': output_val,
                })
            else:
                if output_name not in formatted_parameters['outputs']:
                    formatted_parameters['outputs'][output_name] = []
                formatted_parameters['outputs'][output_name].append(
                    format_parameter(output_val))

    for file_elem in task.files:
        for file_name, file_val in file_elem.items():
            if file_name not in formatted_parameters['files']:
                formatted_parameters['files'][file_name] = []
            formatted_parameters['files'][file_name].append({
                'url_name': file_name.replace('.', '_'),
                'value': file_val,
            })

    out = {
        'commands': cg_fmt,
        'formatted_parameters': formatted_parameters,
    }

    return out


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

    # TODO: after element and iterations sorted:
    formatted_resource_use = {}

    page = render_template(
        'task.html',
        id=wid,
        workflow=wk,
        task=task,
        element_idx=element_idx,
        commands=cg_fmt,
    )
    return page


def download_file(url):
    download_path = DOWNLOAD_DIR.joinpath('{}'.format(random.randint(0, 999)))
    r = requests.get(url)
    with download_path.open('wb') as handle:
        handle.write(r.content)
    return download_path


def format_parameter(param):

    if isinstance(param, list):
        param_fmt = format_list(param)
    elif isinstance(param, dict):
        param_fmt = '<table class="param-dict"><tbody>'
        for k, v in param.items():
            param_fmt += '<tr>'
            param_fmt += '<td class="param-dict param-dict-param-name">{}</td>'.format(
                k)
            param_fmt += '<td class="param-dict"><div class="param-dict">{}<div></td>'.format(
                format_parameter(v))
            param_fmt += '</tr>'
        param_fmt += '</tbody></table>'
    elif isinstance(param, np.ndarray):
        if param.ndim == 1:
            param = param[:, None]
        param_fmt = format_arr(param, format_spec='{:.5g}', html=True, html_classes={
            'table': ['ndarray']})
    else:
        param_fmt = '{}'.format(param)

    return param_fmt


def format_args_check(**kwargs):
    """
    Check types of parameters used in `format_arr`, 'format_list' and
    'format_dict' functions.

    """

    if 'depth' in kwargs and not isinstance(kwargs['depth'], int):
        raise ValueError('`depth` must be an integer.')

    if 'indent' in kwargs and not isinstance(kwargs['indent'], str):
        raise ValueError('`indent` must be a string.')

    if 'col_delim' in kwargs and not isinstance(kwargs['col_delim'], str):
        raise ValueError('`col_delim` must be a string.')

    if 'row_delim' in kwargs and not isinstance(kwargs['row_delim'], str):
        raise ValueError('`row_delim` must be a string.')

    if 'dim_delim' in kwargs and not isinstance(kwargs['dim_delim'], str):
        raise ValueError('`dim_delim` must be a string.')

    if 'format_spec' in kwargs and not isinstance(kwargs['format_spec'],
                                                  (str, list)):
        raise ValueError('`format_spec` must be a string or list of strings.')

    if 'assign' in kwargs:

        if not isinstance(kwargs['assign'], str):
            raise ValueError('`assign` must be a string.')


def format_arr(arr, depth=0, indent='\t', col_delim='\t', row_delim='\n',
               dim_delim='\n', format_spec='{}', html=False, html_classes=None,
               _nested_call=False):
    """
    Get a string representation of a Numpy array, formatted with indents.

    Parameters
    ----------
    arr : ndarray or list of ndarray
        Array of any shape to format as a string, or list of arrays whose
        shapes match except for the final dimension, in which case the arrays
        will be formatted horizontally next to each other.
    depth : int, optional
        The indent depth at which to begin the formatting.
    indent : str, optional
        The string used as the indent. The string which indents each line of
        the array is equal to (`indent` * `depth`).
    col_delim : str, optional
        String to delimit columns (the innermost dimension of the array).
        Default is tab character, \\t.
    row_delim : str, optional
        String to delimit rows (the second-innermost dimension of the array).
        Defautl is newline character, \\n.
    dim_delim : str, optional
        String to delimit outer dimensions. Default is newline character, \\n.
    format_spec : str or list of str, optional
        Format specifier for the array or a list of format specifiers, one for 
        each array listed in `arr`.
    html : bool, optional
        If True, return nested HTML table elements.
    html_classes : dict, optional
        CSS classes to add to HTML table elements.

    Returns
    -------
    str

    """

    # Validation:
    format_args_check(depth=depth, indent=indent, col_delim=col_delim,
                      row_delim=row_delim, dim_delim=dim_delim,
                      format_spec=format_spec)

    if isinstance(arr, np.ndarray):
        arr = [arr]

    if html_classes is None:
        html_classes = {}

    out_shape = list(set([i.shape[:-1] for i in arr]))

    if len(out_shape) > 1:
        raise ValueError('Array shapes must be identical apart from the '
                         'innermost dimension.')

    if not isinstance(arr, (list, np.ndarray)):
        raise ValueError('Cannot format as array, object is '
                         'not an array or list of arrays: type is {}'.format(
                             type(arr)))

    if isinstance(format_spec, str):
        format_spec = [format_spec] * len(arr)

    elif isinstance(format_spec, list):

        fs_err_msg = ('`format_spec` must be a string or list of N strings '
                      'where N is the number of arrays specified in `arr`.')

        if not all([isinstance(i, str)
                    for i in format_spec]) or len(format_spec) != len(arr):
            raise ValueError(fs_err_msg)

    arr_list = arr
    out = ''
    dim_seps = ''
    d = arr_list[0].ndim

    html_table = '<table class="{}">'.format(' '.join(html_classes.get('table', [])))
    html_table_inner = '<table class="inner {}">'.format(
        ' '.join(html_classes.get('table', [])))
    html_tr = '<tr class="{}">'.format(' '.join(html_classes.get('tr', [])))
    html_td = '<td class="{}">'.format(' '.join(html_classes.get('td', [])))

    if d == 1:
        out += (indent * depth)
        if html:
            out += html_tr
        for sa_idx, sub_arr in enumerate(arr_list):
            for col_idx, col in enumerate(sub_arr):
                if html:
                    out += html_td
                out += format_spec[sa_idx].format(col)
                if html:
                    out += '</td>'
                else:
                    if (col_idx < len(sub_arr) - 1):
                        out += col_delim
        if html:
            out += '</tr>'
        else:
            out += row_delim

    else:

        if d > 2:
            dim_seps = dim_delim * (d - 2)

        sub_arr = []
        for i in range(out_shape[0][0]):

            sub_arr_lst = []
            for j in arr_list:
                sub_arr_lst.append(j[i])

            sub_arr.append(format_arr(sub_arr_lst, depth, indent, col_delim,
                                      row_delim, dim_delim, format_spec, html=html,
                                      html_classes=html_classes, _nested_call=True))

        if html:
            if d > 2:
                sub_arr = [html_tr + html_td + i + '</td></tr>' for i in sub_arr]
            if _nested_call:
                table_tag = html_table_inner
            else:
                table_tag = html_table
            sub_arr_joined = ''.join(sub_arr)
            out = table_tag + sub_arr_joined + '</table>'
        else:
            out = dim_seps.join(sub_arr)

    return out


def format_list(lst, depth=0, indent='\t', assign='=', arr_kw=None):
    """
    Get a string representation of a nested list, formatted with indents.

    Parameters
    ----------
    lst : list
        List to format as a string. The list may contain other nested lists,
        nested dicts and Numpy arrays.
    depth : int, optional
        The indent depth at which to begin the formatting.
    indent : str, optional
        The string used as the indent. The string which indents each line is
        equal to (`indent` * `depth`).
    assign : str, optional
        The string used to represent the assignment operator.
    arr_kw : dict, optional
        Array-specific keyword arguments to be passed to `format_arr`. (See 
        `format_arr`)

    Returns
    -------
    str

    """

    if arr_kw is None:
        arr_kw = {}

    format_args_check(depth=depth, ident=indent, assign=assign)

    # Disallow some escape character in `assign` string:
    assign = assign.replace('\n', r'\n').replace('\r', r'\r')

    out = ''
    for elem in lst:
        if isinstance(elem, dict):
            out += (indent * depth) + '{\n' + \
                format_dict(elem, depth + 1, indent, assign, arr_kw) + \
                (indent * depth) + '}\n'

        elif isinstance(elem, list):
            out += (indent * depth) + '[\n' + \
                format_list(elem, depth + 1, indent, assign, arr_kw) + \
                (indent * depth) + ']\n'

        elif isinstance(elem, np.ndarray):
            out += (indent * depth) + '*[\n' + \
                format_arr(elem, depth + 1, indent, **arr_kw) + \
                (indent * depth) + ']\n'

        elif isinstance(elem, (int, float, str)):
            out += (indent * depth) + '{}\n'.format(elem)

        else:
            out += (indent * depth) + '{!r}\n'.format(elem)

    return out


def format_dict(d, depth=0, indent='\t', assign='=', arr_kw=None):
    """
    Get a string representation of a nested dict, formatted with indents.

    Parameters
    ----------
    d : dict
        Dict to format as a string. The dict may contain other nested dicts,
        nested lists and Numpy arrays.
    depth : int, optional
        The indent depth at which to begin the formatting
    indent : str, optional
        The string used as the indent. The string which indents each line is
        equal to (`indent` * `depth`).
    assign : str, optional
        The string used to represent the assignment operator.
    arr_kw : dict, optional
        Array-specific keyword arguments to be passed to `format_arr`. (See 
        `format_arr`)

    Returns
    -------
    str

    """

    if arr_kw is None:
        arr_kw = {}

    format_args_check(depth=depth, indent=indent, assign=assign)

    # Disallow some escape character in `assign` string:
    assign = assign.replace('\n', r'\n').replace('\r', r'\r')

    out = ''
    for k, v in sorted(d.items()):

        if isinstance(v, dict):
            out += (indent * depth) + '{} '.format(k) + assign + ' {\n' + \
                format_dict(v, depth + 1, indent, assign, arr_kw) + \
                (indent * depth) + '}\n'

        elif isinstance(v, list):
            out += (indent * depth) + '{} '.format(k) + assign + ' [\n' + \
                format_list(v, depth + 1, indent, assign, arr_kw) + \
                (indent * depth) + ']\n'

        elif isinstance(v, np.ndarray):
            out += (indent * depth) + '{} '.format(k) + assign + ' *[\n' + \
                format_arr(v, depth + 1, indent, **arr_kw) + \
                (indent * depth) + ']\n'

        elif isinstance(v, (int, float, str)):
            out += (indent * depth) + '{} '.format(k) + \
                assign + ' {}\n'.format(v)

        else:
            out += (indent * depth) + '{} '.format(k) + \
                assign + ' {!r}\n'.format(v)

    return out


if __name__ == '__main__':

    port = 5000
    url = "http://127.0.0.1:{0}".format(port)

    if 'WERKZEUG_RUN_MAIN' not in os.environ:
        threading.Timer(1.25, lambda: webbrowser.open(url)).start()
    app.secret_key = 'super secret key'
    app.run(port=port, debug=True)
