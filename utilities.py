from functools import wraps
from flask import request, make_response, current_app

import logging
from pathlib import Path
from datetime import datetime
import re

''' auth_required decorator is used for showing basic http login dialog for every route'''
def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # the fuction start with request.authirzation is None
        # so it will jump to the Else statement
        # at Else statement, we make a basic login dialog by using make_response with custom header WWW-Authenticate
        if request.authorization and request.authorization.username == current_app.config['APP_USERNAME'] and request.authorization.password == current_app.config['APP_PASSWORD']:
            return f(*args, **kwargs)
        else:
            resp = make_response(f(*args, **kwargs), 401)
            resp.headers['WWW-Authenticate'] = 'Basic realm="Login Required"'
        return resp
    return decorated

''' 
Custom logger is used for creating a custom logger and a file handler for writing log message to a temporary file, 
After that we can push those file back into the html page
'''
def customize_logger(fuction_name):
    # create file if not exist
    current_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    file_log_name =  f'{fuction_name}_{current_time}.log'
    file_log_location = Path.joinpath(Path.cwd().parent, '.tmp', file_log_name)
    file_log_location.parent.mkdir(exist_ok=True)
    f = open(file_log_location, 'w')
    f.close()

    # start a logger and a file handler with a created file
    custom_logger = logging.getLogger('custom')
    file_log = logging.FileHandler(filename=file_log_location)
    file_log.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    file_log.setLevel(logging.DEBUG)
    custom_logger.addHandler(file_log)
    custom_logger.setLevel(logging.DEBUG)
    custom_logger.propagate = True
    return custom_logger, file_log_location

# custom_logger, file_location = customize_logger(fuction_name='git_check')
# with open(file_location, 'r') as f:
#     log = f.read()
#     log = log.replace('\n', '<br>')


def text_formatter(text, command=None):
    message = text.replace('\\n', '<br> &nbsp;&nbsp;&nbsp;&nbsp;')
    current_time = datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
    message = f"{current_time} -- {message}"
    if command:
        message = f"<br><br>COMMAND: {command} with result as: <br> &nbsp;&nbsp;&nbsp;&nbsp; {message}"
    return message