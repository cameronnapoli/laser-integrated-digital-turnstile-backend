import json
import os


def fail_response(msg):
    return json.dumps({"success": False,
                       "error": str(msg)})


def success_response():
    return json.dumps({"success": True})


def verify_token(t):
    """ Verify authorization token """
    # TODO: Complete authentication functionality
    return True


def fetch_credentials():
    """ Get SQL credentials from environment variables """
    return (os.environ['MYSQL_SERVER'], os.environ['MYSQL_USER'],
            os.environ['MYSQL_PASS'], os.environ['MYSQL_DB'])


def set_debug_db():
    """ Point db to local db if on debug """
    os.environ['MYSQL_SERVER'] = '127.0.0.1'
    os.environ['MYSQL_USER'] = 'root'
    os.environ['MYSQL_PASS'] = ''
    os.environ['MYSQL_DB'] = 'lidt'
