import os
from pathlib import Path

import jinja2_highlight
from flask import Flask

DOWNLOAD_DIR = Path(__file__).parent.joinpath('downloaded')
DB_PATH = Path(__file__).parent.joinpath('workflows.sqlite')
GITHUB_REPO_NAME = None # 'aplowman/matflow-workflows'
WORKFLOW_SEARCH_DIR = DOWNLOAD_DIR # r'C:\Users\adamj\dropbox\sims_db\matflow\archived'
GH_TOKEN = os.getenv('GH_TOKEN')
ALLOWED_EXTENSIONS = {'hdf5'}


class MyFlask(Flask):
    jinja_options = dict(Flask.jinja_options)
    jinja_options.setdefault('extensions',
                             []).append('jinja2_highlight.HighlightExtension')


app = MyFlask(__name__, instance_relative_config=True)
app.config.from_object('config')
app.config['UPLOAD_FOLDER'] = DOWNLOAD_DIR

from matflow_viewer import views  # At the end to prevent circular import
