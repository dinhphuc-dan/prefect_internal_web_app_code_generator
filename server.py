from flask import Flask, render_template, request, redirect, make_response, Response, url_for, session
from utilities import auth_required, text_formatter
from dotenv import load_dotenv

from prefect_dbt_core_orchestration import GeneratePrefectDbtCoreJinjaTemplate
from waitress import serve
from pathlib import Path
import subprocess


load_dotenv()
app = Flask(__name__)
app.config.from_prefixed_env()
app.secret_key = "DataTeamForever"

@app.route("/", methods=['GET', 'POST'])
@auth_required
# using decorator auth_required to show login dialog
def login():
    return render_template('login.html')

@app.route("/git_check", methods=['GET', 'POST'])
@auth_required
# using decorator auth_required to show login dialog
def git_check(clicked_button_status=None):
    action_name = 'Git Check'
    # when user click button, flask will send a post request
    clicked_button_status = request.form.get('check_button')
    if request.method == 'POST' and clicked_button_status == 'true':
        try:
            path_to_git = Path.cwd() / 'prefect_dbt_core_orchestration'

            command = f'git status'
            run = subprocess.run(command, shell=True, cwd=path_to_git, capture_output=True, check=True)
            log = text_formatter(command=command, text=repr(run))

            command = f'git pull'
            run = subprocess.run(command, shell=True, cwd=path_to_git, capture_output=True, check=True)
            log = log + text_formatter(command=command, text=repr(run))
                                 
            command = f'git ls-files'
            run = subprocess.run(command, shell=True, cwd=path_to_git, capture_output=True, check=True)
            log = log + text_formatter(command=command, text=repr(run))
                                 
            action_status = 'Succeeded'
        except Exception as e:
            try:
                log = text_formatter(repr(e.stderr))
            except AttributeError:
                log = text_formatter(repr(e))
            action_status = 'Failed'
        return render_template('git_check.html', log=log, action_status =action_status, action_name = action_name )
    else:
    # when user refresh page, flask will send a get request
        return render_template('login.html')


''' This section is for Prefect DBT Core Deployment '''

@app.route("/generate_prefect_dbt_core_template", methods=['GET', 'POST'])
@auth_required
# using decorator auth_required to show login dialog
def generate_prefect_dbt_core_template():
    action_name = 'Generate Template'
    clicked_button_status = request.form.get('generate_prefect_dbt_core_button', None)
    # when user click button, flask will send a post request
    if request.method == 'POST' and clicked_button_status == 'true':
        try:
            # getting value dbt_core_object_name_in_prefect when user fills form and remove any whitespace
            dbt_core_object_name_in_prefect: str = request.form['dbt_core_object_name_in_prefect'].strip()

            dbt_object = GeneratePrefectDbtCoreJinjaTemplate(
                dbt_core_object_name=dbt_core_object_name_in_prefect
            )
            
            command = f'generate prefect dbt temmplate'
            dbt_object.generate_prefect_dbt_core_jinja_template()
            log = text_formatter(command=command, text='generate prefect dbt temmplate succeessfully')

            command = f'push generated file to github'
            run = dbt_object.push_generated_template_to_prefect_agent_dbt_github()
            log =  log + text_formatter(command=command, text=repr(run))

            session['generated_file_name'] = dbt_object.file_name
            session['generated_file_location'] = str(dbt_object._write_file_location)

            action_status = 'Succeeded'
        except Exception as e:
            try:
                log = text_formatter(repr(e.stderr))
            except AttributeError:
                log = text_formatter(repr(e))
            action_status = 'Failed'
        return render_template('generate_prefect_dbt_core_template.html', log=log, action_name=action_name,action_status=action_status)
    # when user refresh page, flask will send a get request
    else:
        return redirect(url_for('git_check'))
    
@app.route("/deploy_dbt_command_to_prefect", methods=['GET', 'POST'])
@auth_required
# using decorator auth_required to show login dialog
def deploy_dbt_command_to_prefect():
    action_name = 'Deploy Dbt Command to Prefect'
    clicked_button_status = request.form.get('deploy_to_prefect', None)
    # when user click button, flask will send a post request
    if request.method == 'POST' and clicked_button_status == 'true':
        try:
            if request.form['dbt_command'].strip(): 
                dbt_command =  request.form['dbt_command'].strip()
                command = f'python {session.get("generated_file_name")} --deploy true --command "{dbt_command}" '
                run = subprocess.run(command, shell=True, cwd=Path(session.get('generated_file_location')), capture_output=True, check=True)
                log = text_formatter(command= command, text=repr(run))
                action_status = 'Succeeded'
            else:
                raise ValueError('Please enter dbt command')
        except Exception as e:
            try:
                log = text_formatter(repr(e.stderr))
            except AttributeError:
                log = text_formatter(repr(e))
            action_status = 'Failed'
        return render_template('deploy_dbt_command_to_prefect.html', log=log, action_name=action_name,action_status=action_status)
    # when user refresh page, flask will send a get request
    else:
        return redirect(url_for('generate_prefect_dbt_core_template'))


''' This section is for Prefect Airbyte Deployment '''





if __name__ == "__main__":
    app.run(
            debug=True,
            host='0.0.0.0',
            port=9090
    )



# test
    
    # dbt_core_operation_name_in_prefect = "test-dbt-core"
    # dbt_object = GeneratePrefectDbtCoreJinjaTemplate(
    #             dbt_core_object_name=dbt_core_operation_name_in_prefect
    #         )
    # print(dbt_object._write_file_location)
    # dbt_object.generate_prefect_dbt_core_jinja_template()
    # # dbt_object.push_generated_template_to_prefect_agent_dbt_github()