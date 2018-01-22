# Flask API for LIDT
#
# Written by:
#   Cameron Napoli
#   Raymond Wang

from flask import Flask, abort, request
from functools import wraps
import MySQLdb as mdb
import sys
import json

app = Flask(__name__)

err_msg = "Invalid Endpoint"
unauth_str = "Unauthorized"


############
## Routes ##
############

# Token based authentication
def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('auth-token')
        print("token: %s" % (token,)) # DEBUG
        if not verify_token(token):
            return unauth_str
        return f(*args, **kwargs)
    return decorated


@app.route("/")
def default():
    return err_msg


@app.route("/gen_auth_token", methods=['POST'])
@auth_required
def gen_auth_token():
    return "gen_auth_token endpoint"


@app.route('/register_event', methods=['POST'])
@auth_required
def register_event():
    ''' Register event (either 'entry' or 'exit')
        from a user device '''
    try:
        print(request.data)
        data = json.loads(request.data)
        event_type = data['eventType']
        # TODO: check if deviceID matches token or
        #       get deviceID using token from db
        device_Id = data['deviceID']
    except ValueError as e:
        return "JSON malformed (JSON cannot be decoded)"
    except KeyError as e:
        return "JSON malformed (Missing required key in object)"

    creds = fetch_credentials()
    sql = ("""INSERT INTO `DeviceEvents`
            (`DeviceID`, `EventType`)
            VALUES (%s, %s); """)
    conn = None
    try:
        conn = mdb.connect(*creds) # unpack creds into params

        cursor = conn.cursor()
        # NOTE: this syntax sanitizes the input for SQL injection
        cursor.execute(sql, (device_Id, event_type))
        conn.commit()
    except mdb.Error, e:
        print("Error %d: %s" % (e.args[0],e.args[1]))
        if conn:
            conn.rollback()
        return ""
    finally:
        if conn:
            conn.close()

    return "register_event endpoint"



######################
## Helper functions ##
######################

def verify_token(t):
    ''' Verify authorization token '''
    return True

def fetch_credentials():
    ''' Get SQL credentials from config file '''
    data = json.load(open('config.json'))
    return (data['server'], data['user'],
            data['pass'], data['db'])



if __name__ == "__main__":
    app.run(port=5000, debug=True)
