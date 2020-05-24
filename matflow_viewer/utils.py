import random
import requests

from github import Github

from matflow_viewer import DOWNLOAD_DIR, GH_TOKEN


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


def download_file(url):
    download_path = DOWNLOAD_DIR.joinpath('{}'.format(random.randint(0, 999)))
    r = requests.get(url)
    with download_path.open('wb') as handle:
        handle.write(r.content)
    return download_path
