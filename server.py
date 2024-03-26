from flask import Flask, render_template, request, redirect, url_for, session
from utilities import auth_required, text_formatter
from dotenv import load_dotenv


from waitress import serve
from pathlib import Path
import subprocess
import os

from prefect_dbt_core_orchestration import GeneratePrefectDbtCoreJinjaTemplate
from prefect_airbyte_connections_orchestration import GeneratePrefectAirbyteJinjaTemplate

# for local testing
load_dotenv()

app = Flask(__name__)
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
    prefect_airbyte_clicked_button_status = request.form.get('prefect_airbyte_check_button', None)
    prefect_dbt_clicked_button_status = request.form.get('prefect_dbt_check_button',None)

    if request.method == 'POST':
        if prefect_airbyte_clicked_button_status == 'true':
            path_to_git = Path.cwd() / 'test_prefect_airbyte_orchestration'
            action_name = action_name + ' Prefect Airbyte'
        elif prefect_dbt_clicked_button_status == 'true':
            path_to_git = Path.cwd() / 'prefect_dbt_core_orchestration'
            action_name = action_name + ' Prefect Dbt Core'

        try:
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
            log = text_formatter(command=command, text=f'generate file {dbt_object.file_name} Succeessfully')

            command = f'push generated file to github'
            run = dbt_object.push_generated_template_to_prefect_agent_dbt_github()
            log =  log + text_formatter(command=command, text=repr(run))

            session['prefect_dbt_generated_file_name'] = dbt_object.file_name
            session['prefect_dbt_generated_file_location'] = str(dbt_object._write_file_location)

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
                command = f'python {session.get("prefect_dbt_generated_file_name")} --deploy true --command "{dbt_command}" '
                run = subprocess.run(command, shell=True, cwd=Path(session.get('prefect_dbt_generated_file_location')), capture_output=True, check=True)
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
@app.route("/generate_prefect_airbyte_template", methods=['GET', 'POST'])
@auth_required
# using decorator auth_required to show login dialog
def generate_prefect_airbyte_template():
    action_name = 'Generate Template'
    clicked_button_status = request.form.get('generate_prefect_airbyte_button', None)
    # when user click button, flask will send a post request
    if request.method == 'POST' and clicked_button_status == 'true':
        try:
            # getting value airbyte_object_name_in_prefect when user fills form and remove any whitespace
            airbyte_object_name_in_prefect: str = request.form['airbyte_object_name_in_prefect'].strip() 

            airbyte_object = GeneratePrefectAirbyteJinjaTemplate(
                airbyte_object_name=airbyte_object_name_in_prefect
            )
            
            command = f'generate prefect airbyte temmplate'
            airbyte_object.generate_prefect_airbyte_jinja_template()
            log = text_formatter(command=command, text=f'generate file {airbyte_object.file_name} Succeessfully')

            command = f'push generated file to github'
            run = airbyte_object.push_generated_template_to_prefect_airbyte_github()
            log =  log + text_formatter(command=command, text=repr(run))

            session['prefect_airbyte_generated_file_name'] = airbyte_object.file_name
            session['prefect_airbyte_generated_file_location'] = str(airbyte_object._write_file_location)

            action_status = 'Succeeded'

        except Exception as e:
            try:
                log = text_formatter(repr(e.stderr))
            except AttributeError:
                log = text_formatter(repr(e))
            action_status = 'Failed'
        return render_template('generate_prefect_airbyte_template.html', log=log, action_name=action_name,action_status=action_status)
    # when user refresh page, flask will send a get request
    else:
        return redirect(url_for('git_check'))

@app.route("/deploy_airbyte_flow_to_prefect", methods=['GET', 'POST'])
@auth_required
# using decorator auth_required to show login dialog
def deploy_airbyte_flow_to_prefect():
    action_name = 'Deploy Airbyte Flow to Prefect'
    clicked_button_status = request.form.get('deploy_to_prefect', None)
    # when user click button, flask will send a post request
    if request.method == 'POST' and clicked_button_status == 'true':
        try:
            command = f'python {session.get("prefect_airbyte_generated_file_name")} --deploy "true" '
            run = subprocess.run(command, shell=True, cwd=Path(session.get('prefect_airbyte_generated_file_location')), capture_output=True, check=True)
            log = text_formatter(command= command, text=repr(run))
            action_status = 'Succeeded'
        except Exception as e:
            try:
                log = text_formatter(repr(e.stderr))
            except AttributeError:
                log = text_formatter(repr(e))
            action_status = 'Failed'
        return render_template('deploy_airbyte_flow_to_prefect.html', log=log, action_name=action_name,action_status=action_status)
    # when user refresh page, flask will send a get request
    else:
        return redirect(url_for('generate_prefect_airbyte_template'))



if __name__ == "__main__":
    # load env variables
    app.config.from_prefixed_env()
    app.secret_key =os.getenv('SESSION_SECRET_KEY')
    serve(app, host="0.0.0.0", port=9090)
    
    
    # local test
    # app.run(
    #         debug=True,
    #         host='0.0.0.0',
    #         port=9090
    # )