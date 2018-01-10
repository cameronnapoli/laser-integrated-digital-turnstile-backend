# Flask API for LIDT
#
# Written by:
#   Cameron Napoli
#   Raymond Wang

from flask import Flask, abort, request
from functools import wraps
import MySQLdb as mdb
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
        token = ''
        if not verify_token(token):
            return unauth_str
        return f(*args, **kwargs)
    return decorated


@app.route("/")
def default():
    global err_msg
    return err_msg


@app.route("/gen_auth_token", methods=['POST'])
@auth_required
def gen_auth_token():
    return "gen_auth_token endpoint"


@app.route('/register_event', methods=['POST'])
def register_event():
    ''' Register event (either 'entry' or 'exit')
        from a user device
    '''
    data = request.data
    creds = fetch_credentials()
    sql = "SELECT VERSION();"
    conn = None
    try:
        conn = mdb.connect(*creds) # unpack creds into params
        cursor = conn.cursor()
        cursor.execute(sql)
    except mdb.Error, e:
        print "Error %d: %s" % (e.args[0],e.args[1])
        sys.exit(1)
    finally:
        if conn:
            conn.close()

    return "register_event endpoint"



######################
## Helper functions ##
######################

def verify_token(t):
    return False

def fetch_credentials():
    data = json.load(open('config.json'))
    return (data['server'], data['user'],
            data['pass'], data['db'])



if __name__ == "__main__":
    app.run(port=5000, debug=True)
