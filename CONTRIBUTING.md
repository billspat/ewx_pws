# Contributing

This document is for Enviroweather staff to get setup and to work on this code base.   We use our institutions Gitlab install for issue tracking and merge requests

## Overview of Process

 - in the gitlab project, create an issue with a number N and/or pick an issue to work on
     - check the current milestone to help prioritize which issues have priority
 - in gitlab, assign the issue to yourself (using the 'assignees' option in top right)
 - in your computer, create a branch for the issue ( on local computer), prefixed with number N
     - for example issue "42: fix flux capacitor" branch could be named "42-flux-capacitor" 
 - code to address the issue in your local, and add commits as you add functionality
     - commits aren't backups but should be for completed pieces of functionality.  Use a backup system to keep a backup of your incompleted work
 - add tests as you go for in local branch
 - push branch to project with the "-u" option (tracking branch) when 1)you have significant functionality you want to have reviewed or share or 2) it's done  and tests pass
 - add comments to the gitlab issue if there are problems, need to ask questions, propose ideas or code to solve, etc
 - if the main branch has been updated while you are working in this branch, frequently use 'git rebase' to update your branch to contain the latest code from main.  The goal is that when your brn
 - when tests are passing and issue is addressed create a merge request for branch from main
 - someone reviews code and merges into main, squashing commits and re-write commit message "fixes #N"
 - once all the working code in the branch is incorporated into the main branch, delete branch in git project
 - close any issues related to the branch/merge request, make a note in the issue which MR/commit is most relevant
 
## Creating issues in gitlab

### File Issue for fix

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

### File issue for new features

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.

### Documentation

to be written: how to edit the documentation


## Set up

Here's how to set up `ewx_pws` for local development.

0. Install the python `poetry` utility which aids development by helping to manage dependencies and create a build system.  This replaces the standard `pip install -r requirements.txt` process See https://python-poetry.org/ for detail.    This is installed system wide, not necessaryly part of an environment 
1. Download a copy of `ewx_pws` locally.
2. Install `ewx_pws` using `poetry`:

    ```console
    $ poetry install
    ```

Note this project may switch to a different build system in the future. 


## Coding

1. Use `git` (or similar) to create a branch for local development and make your changes:

    ```console
    $ git checkout -b branch-starting-with-issuenum
    ```

2. When you're done making changes, check that your changes conform to any code formatting requirements. 

`git commit -m "what problem did you just code"`

1.  Push your branch to the gitlab repository

    ```console
    git push -u origin branch-starting-with-issuenum
    ``` 

## Testing

Write and run tests continually

Note: some tests require a configuration file of station API log-in secrets.  Create a CSV file of station configurations based on project documentation.   Without the file some tests will fail but you can still run 

From the top directory, run

`pytest tests/`


## Building

To build a wheel for ewx_pws, navigate to the top of the directory. Using `poetry` either use
1. Build both a wheel and a tarball without the format option
    ```console
    $ poetry build
    ```
    or
2. Build a wheel only using
    ```console
    $ poetry build --format=wheel
    ```
The output will appear in the `/dist` subdirectory.

## building documentation

The documentation is based on Sphinx, and is a collection of markdown-formatted files, both in the root dir and `/doc` directory.  
this includes a python notebook with some explanatory code.   

### Requirements for building documentation

There is a `docs/requirements.txt` for packages need to compile the document to HTML.   Running

`pip install -r `docs/requirements.txt` 

In addition the ipython notebook requires an environment configuration file (as it does not use the CSV format yet), 
to build the documentation, ensure there is a copy of the configuration file (.env) in the `./docs` directory (for now)

### building

You can build the docs in 3 ways using the terminal

first, `cd docs`

1. if you have `make` installed (MacOS, Linux)

in the docs folder
```
make clean
make html
```

2. If you are using Windows

(untested)
in the docs folder `cmd make.bat`

3. Using the sphinx command

```
rm -rf _build/*
SPHINXPROJ=ewx_pws python -m sphinx . _build
```

The documentation will be in the `./docs/_build/html` folder


## Using the CLI to get weather data

`python bin/getweather.py /path/to/stationlist.csv`

