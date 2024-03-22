from flask import Flask, render_template, request, redirect, make_response, Response
from utilities import auth_required, text_formatter
from dotenv import load_dotenv

from prefect_dbt_core_jinja_code_generator import GeneratePrefectDbtCoreJinjaTemplate
from waitress import serve
from pathlib import Path


load_dotenv()
app = Flask(__name__)
app.config.from_prefixed_env()

@app.route("/", methods=['GET', 'POST'])
@auth_required
# using decorator auth_required to show login dialog
def login():
    return render_template('login.html')
    
@app.route("/generate_prefect_airbyte_template", methods=['GET', 'POST'])
@auth_required
# using decorator auth_required to show login dialog
def generate_prefect_airbyte_template():
    # when user click button, flask will send a post request, therefore we show the git_check html page
    if request.method == 'POST' and request.form['check_button'] == 'true':
        try:
            dbt_core_object_name_in_prefect: str = "test-dbt-core-1"
            dbt_object = GeneratePrefectDbtCoreJinjaTemplate(
                dbt_core_object_name_in_prefect
            )
            dbt_object.generate_prefect_dbt_core_jinja_template()
            git_check_status = 'Git Check Success'
            log = text_formatter('There is no Error while checking git status')
        except Exception as e:
            git_check_status = 'Git Check Error'
            log = text_formatter(e)
        return render_template('git_check.html', log=log, git_check_status =git_check_status)
    # when user refresh page, flask will send a get request, therefore we show the login html page
    else:
        return render_template('login.html')
    
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

@app.route("/generate_prefect_dbt_core_template", methods=['GET', 'POST'])
@auth_required
def generate_prefect_dbt_core_template():
    if request.method == 'POST' and request.form['generate_prefect_dbt_core_template'] == 'true':
        if request.form['dbt_core_object_name_in_prefect']:
            try: 
                dbt_core_object_name_in_prefect: str = request.form['dbt_core_object_name_in_prefect']
                dbt_object = GeneratePrefectDbtCoreJinjaTemplate(
                    dbt_core_object_name_in_prefect
                )
                dbt_object.generate_prefect_dbt_core_jinja_template()
                generate_template_status = 'true'
                log = text_formatter('There is no Error while generating template')
            except Exception as e:
                generate_template_status = 'false'
                log = text_formatter(e)
            return render_template('generate_template.html', log=log, check_status =generate_template_status)
        else: 
            generate_template_status = 'false'
            log = text_formatter('There is no Error while generating template')
            return render_template('generate_template.html', log=log, check_status =generate_template_status)



if __name__ == "__main__":
    app.run(
            debug=True,
            host='0.0.0.0',
            port=9090
    )