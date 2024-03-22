from flask import Flask, render_template, request, redirect, make_response, Response, url_for
from utilities import auth_required, text_formatter
from dotenv import load_dotenv

from prefect_dbt_core_orchestration import GeneratePrefectDbtCoreJinjaTemplate
from waitress import serve
from pathlib import Path
import subprocess
from pathlib import Path


load_dotenv()
app = Flask(__name__)
app.config.from_prefixed_env()

@app.route("/", methods=['GET', 'POST'])
@auth_required
# using decorator auth_required to show login dialog
def login():
    return render_template('login.html')

@app.route("/git_check", methods=['GET', 'POST'])
@auth_required
# using decorator auth_required to show login dialog
def git_check():
    # when user click button, flask will send a post request, therefore we show the git_check html page
    if request.method == 'POST' and request.form['check_button'] == 'true':
        try:
            command = f'git status && git pull'
            path_to_git = Path.cwd() / 'prefect_dbt_core_orchestration'
            run = subprocess.run(command, shell=True, cwd=path_to_git, capture_output=True)
            git_check_status = 'Git Check Success'
            log = text_formatter(f'{run}')
        except Exception as e:
            git_check_status = 'Git Check Error'
            log = text_formatter(e)
        return render_template('git_check.html', log=log, git_check_status =git_check_status)
    else:
        return render_template('login.html')
    
@app.route("/generate_prefect_dbt_core_template", methods=['GET', 'POST'])
@auth_required
# using decorator auth_required to show login dialog
def generate_prefect_airbyte_template():
    # when user click button, flask will send a post request, therefore we show the git_check html page
    if request.method == 'POST' and request.form['generate_prefect_dbt_core_button'] == 'true':
        try:
            dbt_core_object_name_in_prefect: str = request.form['dbt_core_object_name_in_prefect']
            print(dbt_core_object_name_in_prefect)
            dbt_object = GeneratePrefectDbtCoreJinjaTemplate(
                dbt_core_object_name_in_prefect
            )
            print(f'before generate template')
            dbt_object.generate_prefect_dbt_core_jinja_template()
            print(f'after generate template')
            dbt_object.push_generated_template_to_prefect_agent_dbt_github()
            git_check_status = 'Git Check Success'
            log = text_formatter('There is no Error generate file and push to github')
        except Exception as e:
            git_check_status = 'Git Check Error'
            log = text_formatter(e)
        return render_template('generate_prefect_dbt_core_template.html', log=log, git_check_status =git_check_status)
    # when user refresh page, flask will send a get request, therefore we show the login html page
    else:
        return redirect(url_for('git_check'))
    
# @app.route("/generate_prefect_airbyte_template", methods=['GET', 'POST'])
# @auth_required
# # using decorator auth_required to show login dialog
# def generate_prefect_airbyte_template():
#     # when user click button, flask will send a post request, therefore we show the git_check html page
#     if request.method == 'POST' and request.form['check_button'] == 'true':
#         try:
#             dbt_core_object_name_in_prefect: str = "test-dbt-core-1"
#             dbt_object = GeneratePrefectDbtCoreJinjaTemplate(
#                 dbt_core_object_name_in_prefect
#             )
#             dbt_object.generate_prefect_dbt_core_jinja_template()
#             git_check_status = 'Git Check Success'
#             log = text_formatter('There is no Error while checking git status')
#         except Exception as e:
#             git_check_status = 'Git Check Error'
#             log = text_formatter(e)
#         return render_template('git_check.html', log=log, git_check_status =git_check_status)
#     # when user refresh page, flask will send a get request, therefore we show the login html page
#     else:
#         return render_template('login.html')


if __name__ == "__main__":
    app.run(
            debug=True,
            host='0.0.0.0',
            port=9090
    )