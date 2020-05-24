from setuptools import setup, find_packages

setup(
    name='matflow-viewer',
    version='0.1.0',
    install_requires=[
        # 'matflow',
        'jinja2_highlight',
        'pygithub',
        'flask',
    ],
    entry_points={
        'console_scripts': [
            'mfview=run:main',
        ],
    },
    packages=find_packages(),
)
