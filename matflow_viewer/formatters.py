import copy
from datetime import timedelta

import numpy as np
from hpcflow.utils import format_time_delta


def format_task_resources(task):
    res_use = []
    for i in (task.resource_usage or []):

        i = copy.deepcopy(i)
        td = timedelta(**i['duration'])
        i['duration'] = format_time_delta(td)

        res_use.append(i)

    return res_use


def get_task_arguments(task):
    cg_fmt = task.get_formatted_commands()[0]
    formatted_parameters = {
        'inputs': {},
        'outputs': {},
        'files': {},
    }

    for element in task.elements:

        for input_name, input_val in element.inputs.get_all().items():
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

        for output_name, output_val in element.outputs.get_all().items():
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

        for file_name, file_val in element.files.get_all().items():
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
