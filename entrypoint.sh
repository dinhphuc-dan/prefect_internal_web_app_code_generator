#! /bin/bash 

git config --global user.email "120212dinhphuc@isneu.org"
git config --global user.name "phucdinh"
git clone https://${GIT_ACCESS_TOKEN}@github.com/${GIT_PREFECT_DBT_CORE_ORCHESTRATION_NAME}.git
git clone https://${GIT_ACCESS_TOKEN}@github.com/${GIT_PREFECT_AIRBYTE_ORCHESTRATION_NAME}.git
python server.py
