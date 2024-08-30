from flask import Flask, render_template, request, redirect, url_for, session
from utilities import auth_required, text_formatter
from dotenv import load_dotenv


from waitress import serve
from pathlib import Path
import subprocess
import os
import re
import io
from contextlib import redirect_stdout
import argparse

from prefect_dbt_core_orchestration import GeneratePrefectDbtCoreJinjaTemplate
from prefect_airbyte_connections_orchestration import GeneratePrefectAirbyteJinjaTemplate
from superset_automation import Superset, Bigquery, handle_user_input

# for local testing
load_dotenv()

# basic setup for argument throug command line for local testing and development
_parser=argparse.ArgumentParser()
_parser.add_argument("--production")
_args=_parser.parse_args()

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
    superset_automation_button_status = request.form.get('superset_automation',None)

    if request.method == 'POST':
        if prefect_airbyte_clicked_button_status == 'true':
            github_name = re.search(r'\/[\S]+',os.getenv('GIT_PREFECT_AIRBYTE_ORCHESTRATION_NAME')).group().split('/')[1]
            path_to_git = Path.cwd() / github_name
            action_name = action_name + ' Prefect Airbyte'
        elif prefect_dbt_clicked_button_status == 'true':
            github_name = re.search(r'\/[\S]+',os.getenv('GIT_PREFECT_DBT_CORE_ORCHESTRATION_NAME')).group().split('/')[1]
            path_to_git = Path.cwd() / github_name
            action_name = action_name + ' Prefect Dbt Core'
        elif superset_automation_button_status == 'true':
            github_name = re.search(r'\/[\S]+',os.getenv('GIT_SUPERSET_AUTOMATION_NAME')).group().split('/')[1]
            path_to_git = Path.cwd() / github_name
            action_name = action_name + ' Superset Automation'

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

''' This section is for Superset Automation'''
@app.route("/superset_automation_options", methods=['GET', 'POST'])
@auth_required
# using decorator auth_required to show login dialog
def superset_automation_options():
    list_companies = ['govo', 'jacat', 'fidra']
    # when user click button, flask will send a post request
    create_new_roles_and_role_security_button_status = request.form.get('create_new_roles_and_role_security', None)
    update_table_all_role_sercurity_button_status = request.form.get('update_table_all_role_sercurity',None)
    update_mkt_app_permissions_button_status = request.form.get('update_mkt_app_permissions',None)

    if request.method == 'POST':
        if create_new_roles_and_role_security_button_status == 'true':
            list_role_type_options = ['app_related_role', 'mkt_performance_related_role']
            action_name = 'Create New Roles and Role Sercurity'
            action_id = 1
        elif update_table_all_role_sercurity_button_status == 'true':
            list_role_type_options = ['app_related_role', 'mkt_performance_related_role']
            action_name = 'Update Table All Role Sercurities'
            action_id = 2
        elif update_mkt_app_permissions_button_status == 'true':
            list_role_type_options = ['update_permission_mkt_app']
            action_name = 'Update Mkt App Permissions'
            action_id = 3
        return render_template('superset_automation_options.html', 
                               list_role_type_options = list_role_type_options, 
                               action_name = action_name, 
                               list_companies = list_companies,
                               action_id = action_id
        )
    # when user refresh page, flask will send a get request
    else:
        return redirect(url_for('git_check'))

@app.route("/superset_automation_actions_loading", methods=['GET', 'POST'])
@auth_required
# using decorator auth_required to show login dialog
def superset_automation_actions_loading():
    session['superset_role_type_option'] = request.form.get('superset_role_type_options', None)
    session['superset_company'] = request.form.get('superset_company_options', None)
    session['superset_start_date'] = request.form.get('superset_date_input', None)
    session['superest_action_name'] = request.form.get('action_name', None)
    session['superset_action_id'] = request.form.get('action_id', None)
    if request.method == 'POST' and request.form['superset_start_action'] == 'true':
        return render_template('superset_automation_actions_loading.html')


@app.route("/superset_automation_actions_result", methods=['GET', 'POST'])
@auth_required
# using decorator auth_required to show login dialog
def superset_automation_actions_result():
    role_type_option = session.get('superset_role_type_option')
    company = session.get('superset_company')
    start_date = session.get('superset_start_date')
    action_name =  session.get('superest_action_name')
    action_id = session.get('superset_action_id')
    query, list_dataset, row_level_security_id_query_condition, table_id_query_condition, company_name = handle_user_input(fuction_type=role_type_option, company_name=company)
    bg = Bigquery()
    list_object = bg.get_object_from_bigquery(query=query, start_date=start_date)
    superset = Superset(
        base_url= os.getenv('SUPERSET_BASE_URL'),
        username = os.getenv('SUPERSET_USERNAME'),
        password = os.getenv('SUPERSET_PASSWORD') 
    )
    try:
        # getting print message from fuction using redirect_stdout:https://stackoverflow.com/questions/16571150/how-to-capture-stdout-output-from-a-python-function-call
        f = io.StringIO()
        if action_id == '1':
            with redirect_stdout(f):
                superset.create_role(list_object = list_object, list_dataset=list_dataset, table_id_query_condition=table_id_query_condition)
        elif action_id == '2':
            with redirect_stdout(f):
                superset.update_table_all_row_level_security(tables_schema=row_level_security_id_query_condition, list_dataset=list_dataset, table_id_query_condition=table_id_query_condition)
        elif action_id == '3':
            with redirect_stdout(f):
                superset.update_users_app_permission(objects = list_object, company_name = company_name)
        log = text_formatter(text=f.getvalue())
        action_status = 'Succeeded'
    except Exception as e:
        try:
            log = text_formatter(repr(e.stderr))
        except AttributeError:
            log = text_formatter(repr(e))
        action_status = 'Failed'
    return render_template('superset_automation_actions_result.html', log=log, action_name=action_name,action_status=action_status)

if __name__ == "__main__":
    # load env variables
    app.config.from_prefixed_env()
    app.secret_key =os.getenv('SESSION_SECRET_KEY')

    # when use tag --production true  
    # we will run app as in production
    # else run app in testing mode
    if _args.production == 'true':
        serve(app, host="0.0.0.0", port=9090)
    else: 
        app.run(
                debug=True,
                host='0.0.0.0',
                port=9000
        )