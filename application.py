# Flask API for Laser Integrated Digital Turnstile (LIDT)
#   Created on: 2017-12-21
#   Written by: Cameron Napoli

from flask import Flask, abort, request
from flask_cors import CORS, cross_origin
from functools import wraps
from datetime import datetime, timedelta
from calendar import monthrange
import sys, json, math

from helpers import fail_response, success_response, \
                    verify_token, fetch_credentials, set_debug_db
from sql_helpers import sql_insert, sql_select

application = Flask(__name__)
CORS(application)  # allow cross-origin requests


###################
## Device Routes ##
###################

# Token based authentication
def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('auth-token')
        print("token: %s" % (token,))  # DEBUG
        if not verify_token(token):
            return "Unauthorized"
        return f(*args, **kwargs)

    return decorated


@application.route("/")
def default():
    return "Invalid Endpoint"


@application.route("/gen_auth_token", methods=['POST'])
@auth_required
def gen_auth_token():
    return "gen_auth_token endpoint"


@application.route('/register_event', methods=['POST'])
@auth_required
def register_event():
    """ Register event (either 'entry' or 'exit') from a user device """
    try:
        data = json.loads(request.data)
        event_type, device_id = data['eventType'], data['deviceID']
    except ValueError as e:
        return "JSON malformed (JSON cannot be decoded)"
    except KeyError as e:
        return "JSON malformed (Missing required key in object)"

    creds = fetch_credentials()

    sql = "INSERT INTO `DeviceEvents` (`DeviceID`, `EventType`) VALUES (%s, %s); "

    sql_insert(sql, (device_id, event_type))

    return "register_event success"


##################
## Debug Routes ##
##################

@application.route('/debug_preview', methods=['GET'])
def debug_preview():
    """ Function to preview debug info for a specific deviceId """

    html_page = """
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"><title>Debug Preview</title>
        <style type="text/css">* {font-family: sans-serif;}</style></head>
        <body> {0} </body>
    </html>
    """

    sql = """ SELECT `DeviceID`, `CreatedDate`, `EventType`
    FROM `DeviceEvents` WHERE `DeviceID`=%s ORDER BY `CreatedDate` DESC; """

    id_num = request.args["id"]

    results = sql_select(sql, (id_num,))

    if len(results) == 0:
        return html_page % ("No results found in query for deviceId: " + str(id_num))

    entry_count, exit_count, incorrect_count = 0, 0, 0

    for row in results:
        if row[2] == "exit":
            exit_count += 1
        elif row[2] == "entry":
            entry_count += 1
        else:
            incorrect_count += 1

    html_content = ("<h1>ID Num: " + str(id_num) + "</h1><br>" +
                    "<b>Entry count:</b> " + str(entry_count) + "<br>" +
                    "<b>Exit count: </b> " + str(exit_count) + "<br><br>" +
                    "<b>Debug for events:</b><br>")

    for row in results:
        html_content += ("<i>" + str(row[1].strftime("%Y-%m-%d %H:%M:%S")) + "</i>" +
                         "&nbsp;&nbsp;'" + row[2] + "'<br>")

    return html_page.format(html_content)


#########################
## Routes for Frontend ##
#########################

@application.route('/GetAllClientDevices', methods=['GET'])
def GetAllClientDevices():
    """ Just return devices associated with a client """

    client_id = request.args["clientId"]

    try:
        client_id = str(int(client_id))
    except ValueError:
        return fail_response("client_id must be an integer")

    sql = """ SELECT DISTINCT Device.DeviceID FROM Device
                INNER JOIN DeviceEvents ON Device.DeviceID = DeviceEvents.DeviceID
                WHERE Device.ClientID=%s """

    result = []
    sql_results = sql_select(sql, (client_id,))

    for row in sql_results:
        result.append(row[0])

    return json.dumps(result)


@application.route('/GetDeviceCount', methods=['GET'])
def GetDeviceCount():
    """ Get the device count for today """

    device_id = request.args["deviceId"]

    try:
        device_id = str(int(device_id))
    except ValueError:
        return fail_response("device_id must be an integer")

    sql = """ SELECT DeviceID, EventType, COUNT(*) FROM DeviceEvents
              WHERE DeviceID=%s AND CreatedDate > %s AND CreatedDate < %s GROUP BY DeviceID, EventType """

    today = datetime.utcnow().strftime("%Y-%m-%d")
    today_start, today_end = today + " 00:00:00", today + " 23:59:59"

    sql_results = sql_select(sql, (device_id, today_start, today_end))
    result, res_temp = [], {}

    # Compile result in a list of objects to be used on the frontend
    for row in sql_results:
        device_id = row[0]
        if not device_id in res_temp:
            res_temp[device_id] = {"entries": 0, "exits": 0}

        if row[1] == "entry":
            res_temp[device_id]["entries"] = row[2]
        elif row[1] == "exit":
            res_temp[device_id]["exits"] = row[2]
        else:
            print("ERROR: EventType (%s) is not valid" % row[1])

    for device_id in res_temp:
        result.append({"DeviceId": device_id,
                       "Entries": res_temp[device_id]["entries"],
                       "Exits": res_temp[device_id]["exits"]})

    return json.dumps(result)


@application.route('/GetAllDeviceCountHistory', methods=['GET'])
def GetAllDeviceCountHistory():
    """
    endpoint parameters:

        clientId: Id of client to fetch devices for
        interval: ('day' | 'month' | 'year')
        date: 'YYYY-MM-DD' format

            NOTE: depending on the interval, only part of the date string might be used
            e.g. {clientId: 1, interval: 'year', date: '2018-01-02'}
              the function would just find the monthly usage for the 2018 year
    """

    client_id, interval = request.args.get('clientId'), request.args.get('interval')
    specifiedDatetime = request.args.get('date') or ''

    try:
        client_id = int(client_id)
        if interval not in ['day', 'month', 'year']:
            return fail_response("Interval must be one of the following: %s" % str(interval))
        dt = datetime.strptime(specifiedDatetime, "%Y-%m-%d")
    except ValueError as e:
        return fail_response("input error: %s" % str(e))

    sql = """
    SELECT d1.DeviceID AS dID, DeviceEvents.CreatedDate AS CD, DeviceEvents.EventType AS ET FROM
                (SELECT DISTINCT Device.DeviceID FROM Device
                  INNER JOIN DeviceEvents
                  ON Device.DeviceID = DeviceEvents.DeviceID WHERE Device.ClientID=%s)d1
                INNER JOIN DeviceEvents
                    ON DeviceEvents.DeviceID = d1.DeviceID
                        WHERE DeviceEvents.CreatedDate > %s AND DeviceEvents.CreatedDate < %s; """

    buckets = {}

    if interval == 'day':
        t_start, t_end = str(specifiedDatetime) + " 00:00:00", str(specifiedDatetime) + " 23:59:59"

        params = (client_id, t_start, t_end)
        results = sql_select(sql, params)

        num_buckets = 48

        # create "buckets" every 30min so that when data is passed out
        # it can easily be processed by frontend chart code
        for row in results:
            deviceId, createdDate, eventType = row[0], row[1], row[2]

            if deviceId not in buckets:
                buckets[deviceId] = [0] * num_buckets

            minutes = createdDate.minute + (createdDate.hour * 60)
            bucket_loc = int(math.floor(minutes / num_buckets))

            if eventType == 'entry':
                buckets[deviceId][bucket_loc] += 1

        return json.dumps(buckets)

    elif interval == 'month':
        t_start, t_end = datetime(dt.year, dt.month, 1), datetime(dt.year, dt.month + 1, 1)

        params = (client_id, t_start, t_end)
        results = sql_select(sql, params)

        num_buckets = monthrange(dt.year, dt.month)[1]
        print(num_buckets)

        # drop results into buckets for count
        for row in results:
            deviceId, createdDate, eventType = row[0], row[1], row[2]

            if deviceId not in buckets:
                buckets[deviceId] = [0] * num_buckets

            days = createdDate.day - 1
            bucket_loc = int(days)

            if eventType == 'entry':
                buckets[deviceId][bucket_loc] += 1

        return json.dumps(buckets)

    elif interval == 'year':
        t_start = datetime(dt.year, 1, 1)
        t_end = datetime(dt.year + 1, 1, 1)
        # loop through months in that year

        params = (client_id, t_start, t_end)
        results = sql_select(sql, params)

        num_buckets = 12

        # drop results into buckets for count
        for row in results:
            deviceId, createdDate, eventType = row[0], row[1], row[2]

            if deviceId not in buckets:
                buckets[deviceId] = [0] * num_buckets

            months = createdDate.month - 1
            bucket_loc = int(months)

            if eventType == 'entry':
                buckets[deviceId][bucket_loc] += 1

        return json.dumps(buckets)

    else:
        raise Exception("fail_response should have been issued for parameter interval")


@application.route('/AddDevice', methods=['POST'])
def AddDevice():
    """
    endpoint parameters:

        deviceId: id of device to add
        name: string name for device
        location: physical location str
        MACAddress: MAC Address str
    """

    deviceId = request.form.get('deviceId')
    name = request.form.get('name')
    location = request.form.get('location')
    MACAddress = request.form.get('MACAddress')

    try:
        deviceId = str(int(deviceId))
    except ValueError as ve:
        return fail_response("device_id must be an integer: %s" % str(ve))

    sql = """ INSERT INTO Device (DeviceID, CreatedBy, ClientID, Name, MACAddress, Location)
              VALUES ( %s, 0, 1, %s, %s, %s ); """

    try:
        params = (deviceId, name, MACAddress, location)
        sql_insert(sql, params)

    except Exception as e:
        return fail_response(e)

    return success_response()


if __name__ == "__main__":
    port_num = 80

    if len(sys.argv) > 1:
        if sys.argv[1] == '-debug':
            set_debug_db()
            port_num = 5000

    application.debug = True
    application.run(port=port_num)
