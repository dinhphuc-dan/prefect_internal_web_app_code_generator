#! /bin/bash 
git clone https://${GIT_ACCESS_TOKEN}@github.com/${GIT_PREFECT_DBT_CORE_ORCHESTRATION_NAME}.git
pip install -r local-packages.txt --trusted-host pypi.python.org --no-cache-dir
prefect agent start -q Testtete