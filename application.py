# Flask API for LIDT
#
# Written by:
#   Cameron Napoli

from flask import Flask, abort, request
from functools import wraps
import MySQLdb as mdb
import sys
import json
import os
from datetime import datetime

application = Flask(__name__)

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


@application.route("/")
def default():
    return err_msg


@application.route("/gen_auth_token", methods=['POST'])
@auth_required
def gen_auth_token():
    return "gen_auth_token endpoint"


@application.route('/register_event', methods=['POST'])
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

    return "register_event success"


@application.route('/debug_preview', methods=['GET'])
def debug_preview():
    html_page = """
    <!DOCTYPE html>
    <html>
        <head>
            <meta charset="utf-8">
            <title>Debug Preview</title>
            <style type="text/css">
                * {
                    font-family:"Lucida Sans Unicode", "Lucida Grande", sans-serif;
                }
            </style>
        </head>
        <body>
            %s
        </body>
    </html>
    """
    id_num = request.args['id']

    creds = fetch_credentials()
    conn = None
    results = []
    try:
        conn = mdb.connect(*creds) # unpack creds into params
        cursor = conn.cursor()
        sql = """
        SELECT `DeviceID`, `CreatedDate`, `EventType`
        FROM `DeviceEvents`
        WHERE `DeviceID`=%s
        ORDER BY `CreatedDate` DESC;
        """
        cursor.execute(sql, (id_num,))
        results = cursor.fetchall()
    except mdb.Error, e:
        print("Error %d: %s" % (e.args[0],e.args[1]))
        return "Error %d: %s" % (e.args[0],e.args[1])
    finally:
        if conn:
            conn.close()

    if len(results) == 0:
        return html_page % "No results found in query"

    entry_count = 0
    exit_count  = 0
    incorrect_count = 0

    for row in results:
        if row[2] == 'exit':
            exit_count += 1
        elif row[2] == 'entry':
            entry_count += 1
        else:
            incorrect_count += 1

    html_content = ""
    html_content += "<h1>ID Num: "+str(id_num)+"</h1><br>"
    html_content += "<b>Entry count:</b> "+str(entry_count)
    html_content += "<br>"
    html_content += "<b>Exit count: </b> "+str(exit_count)
    html_content += "<br>"
    html_content += "<br>"
    html_content += "<b>Debug for events:</b>"
    html_content += "<br>"

    for row in results:
        html_content += "<i>"+str(row[1].strftime("%Y-%m-%d %H:%M:%S"))+"</i>"
        html_content += "&nbsp;&nbsp;'" + row[2] + "'"
        html_content += "<br>"

    return html_page % html_content


@application.route('/data_dump', methods=['GET', 'POST'])
@auth_required
def data_dump():
    ''' fetch all raw data from events table '''
    creds = fetch_credentials()
    conn = None
    try:
        conn = mdb.connect(*creds) # unpack creds into params
        cursor = conn.cursor()
        sql = """
            SELECT `DeviceID`, `CreatedDate`, `EventType` FROM `DeviceEvents`
            ORDER BY `CreatedDate` DESC;
            """
        results = cursor.execute(sql)
        return str(cursor.fetchall())
    except mdb.Error, e:
        print("Error %d: %s" % (e.args[0],e.args[1]))
        return "Error %d: %s" % (e.args[0],e.args[1])
    finally:
        if conn:
            conn.close()


######################
## Helper functions ##
######################

def verify_token(t):
    ''' Verify authorization token '''
    # TODO: Complete auth
    return True

def fetch_credentials():
    ''' Get SQL credentials from environment variables '''
    return (os.environ['MYSQL_SERVER'],
            os.environ['MYSQL_USER'],
            os.environ['MYSQL_PASS'],
            os.environ['MYSQL_DB'])



if __name__ == "__main__":
    application.debug = True
    application.run(port=80)
