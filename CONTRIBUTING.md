# Contributing

This document is for Enviroweather staff to get setup and to work on this code base.   We use our institutions Gitlab install for issue tracking and merge requests

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

0. Install the python `poetry` utility which aids development.  See https://python-poetry.org/ for detail.    This is installed system wide, not necessaryly part of an environment 
1. Download a copy of `ewx_pws` locally.
2. Install `ewx_pws` using `poetry`:

    ```console
    $ poetry install
    ```

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

Note: some tests require a configuration file of station API log-in secrets.  Create the file .env based on project documentation.   Without the file some tests will fail but you can still run 

From the top directory, run

`pytest tests/`


## Using the CLI to get weather data

`python bin/getweather.py /path/to/stationlist.csv`

