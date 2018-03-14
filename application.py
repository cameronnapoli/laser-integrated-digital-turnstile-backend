# Flask API for LIDT
#
# Written by: Cameron Napoli

from flask import Flask, abort, request
from flask_cors import CORS, cross_origin
from functools import wraps
import MySQLdb as mdb
from datetime import datetime, timedelta
from calendar import monthrange
import sys, os, json, math


application = Flask(__name__)
CORS(application) # allow cross-origin requests

err_msg = "Invalid Endpoint"
unauth_str = "Unauthorized"
def fail_response(msg):
    return json.dumps({ "success": False,
                        "error"  : str(msg) })
def success_response():
    return json.dumps({ "success": True })


###################
## Device Routes ##
###################

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
    """ Register event (either 'entry' or 'exit')
        from a user device """
    # TODO: token based authentication
    try:
        data = json.loads(request.data)
        event_type = data['eventType']
        device_Id = data['deviceID']
    except ValueError as e:
        return "JSON malformed (JSON cannot be decoded)"
    except KeyError as e:
        return "JSON malformed (Missing required key in object)"

    creds = fetch_credentials()

    sql = ("""INSERT INTO `DeviceEvents`
            (`DeviceID`, `EventType`)
            VALUES (%s, %s); """)

    sql_insert(sql, (device_Id, event_type))

    return "register_event success"




##################
## Debug Routes ##
##################

@application.route('/debug_preview', methods=['GET'])
def debug_preview():
    """ Function to preview debug info for certain device, this will
        be deleted later on in development """
    html_page = """
    <!DOCTYPE html>
    <html><head><meta charset="utf-8">
            <title>Debug Preview</title>
            <style type="text/css">
                * {font-family:"Lucida Sans Unicode", "Lucida Grande", sans-serif;}
            </style>
        </head><body> %s </body>
    </html>
    """
    id_num = request.args['id']

    sql = """
    SELECT `DeviceID`, `CreatedDate`, `EventType`
    FROM `DeviceEvents` WHERE `DeviceID`=%s ORDER BY `CreatedDate` DESC;
    """
    results = sql_select(sql, (id_num,))

    if len(results) == 0:
        return html_page % ("No results found in query for deviceId: "+str(id_num))

    entry_count, exit_count, incorrect_count = 0, 0, 0

    for row in results:
        if row[2] == 'exit':
            exit_count += 1
        elif row[2] == 'entry':
            entry_count += 1
        else:
            incorrect_count += 1

    html_content  = "<h1>ID Num: "+str(id_num)+"</h1><br>"
    html_content += "<b>Entry count:</b> "+str(entry_count) + "<br>"
    html_content += "<b>Exit count: </b> "+str(exit_count) + "<br><br>"
    html_content += "<b>Debug for events:</b><br>"

    for row in results:
        html_content += "<i>"+str(row[1].strftime("%Y-%m-%d %H:%M:%S"))+"</i>"
        html_content += "&nbsp;&nbsp;'" + row[2] + "'<br>"

    return html_page % html_content





#########################
## Routes for Frontend ##
#########################

@application.route('/GetAllClientDevices', methods=['GET'])
def GetAllClientDevices():
    """ Just return devices associated with a client """

    clientId = request.args['clientId']

    try:
        clientId = str(int(clientId))
    except ValueError:
        return fail_response("client_id must be an integer")

    sql = """ SELECT DISTINCT Device.DeviceID FROM Device
            INNER JOIN
            DeviceEvents
            ON Device.DeviceID = DeviceEvents.DeviceID
            WHERE Device.ClientID=%s """

    res = []
    results = sql_select(sql, (clientId,))

    for row in results:
        res.append(row[0])
    # print(res)

    return json.dumps(res)

# @application.route('/GetAllClientDevices', methods=['GET'])
# def GetAllClientDevices():
#     """ Get all devices associated with a certain client """
#
#     clientId = request.args['clientId']
#
#     try:
#         clientId = str(int(clientId))
#     except ValueError:
#         return fail_response("client_id must be an integer")
#
#     sql = """ SELECT Device.DeviceID, DeviceEvents.EventType, COUNT(*)
#                 FROM Device INNER JOIN DeviceEvents
#                 ON Device.DeviceID=DeviceEvents.DeviceID
#                 WHERE Device.ClientID=%s
#                 AND DeviceEvents.CreatedDate > %s
#                 AND DeviceEvents.CreatedDate < %s
#                 GROUP BY Device.DeviceID, DeviceEvents.EventType """
#
#     today = datetime.utcnow().strftime("%Y-%m-%d")
#
#
#     # today = "2018-03-02" # DEBUG
#
#
#     today_start = today + " 00:00:00"
#     today_end = today + " 23:59:59"
#
#     results = sql_select(sql, (clientId, today_start, today_end))
#
#     res, res_temp = [], {}
#
#     for row in results:
#         deviceId = row[0]
#         if not deviceId in res_temp:
#             res_temp[deviceId] = {
#                 "entries": 0,
#                 "exits": 0
#             }
#         if row[1] == 'entry':
#             res_temp[deviceId]["entries"] = row[2]
#         elif row[1] == 'exit':
#             res_temp[deviceId]["exits"] = row[2]
#         else:
#             print("ERROR: EventType (%s) is not valid" % row[1])
#
#     for k in res_temp:
#         res.append({
#             "DeviceId": k,
#             "Entries": res_temp[k]["entries"],
# 	        "Exits": res_temp[k]["exits"]
#         })
#
#
#     # [{
#     # 	'DeviceId': deviceId,
#     # 	'Entries': entry_count,
#     # 	'Exits': exit_count
#     # },
#     # {
#     # 	'DeviceId': deviceId,
#     # 	'Entries': entry_count,
#     # 	'Exits': exit_count
#     # }...]
#
#     return json.dumps(res)


@application.route('/GetDeviceCount', methods=['GET'])
def GetDeviceCount():
    """ Get the device count for today """

    deviceId = request.args['deviceId']

    try:
        deviceId = str(int(deviceId))
    except ValueError:
        return fail_response("device_id must be an integer")

    sql = """ SELECT DeviceID, EventType, COUNT(*)
                FROM DeviceEvents
                WHERE DeviceID=%s AND CreatedDate > %s AND CreatedDate < %s
                GROUP BY DeviceID, EventType """

    today = datetime.utcnow().strftime("%Y-%m-%d")

    today_start = today + " 00:00:00"
    today_end = today + " 23:59:59"

    results = sql_select(sql, (deviceId, today_start, today_end))

    res, res_temp = [], {}

    for row in results:
        deviceId = row[0]
        if not deviceId in res_temp:
            res_temp[deviceId] = { "entries": 0,
                                   "exits"  : 0 }
        if row[1] == 'entry':
            res_temp[deviceId]["entries"] = row[2]
        elif row[1] == 'exit':
            res_temp[deviceId]["exits"] = row[2]
        else:
            print("ERROR: EventType (%s) is not valid" % row[1])

    for k in res_temp:
        res.append({ "DeviceId": k,
                     "Entries" : res_temp[k]["entries"],
        	         "Exits"   : res_temp[k]["exits"] })

    return json.dumps(res)


@application.route('/GetAllDeviceCountHistory', methods=['GET'])
def GetAllDeviceCountHistory():
    """ parameters
        ------------------------
            clientId :
            interval : ('day' | 'month' | 'year')
            date : 'YYYY-MM-DD'

                e.g. '2018-01-02'
                  for day it would be find the day usage for '2018-01-02'
                  and for year it would find the 2018 usage for each month
    """

    clientId = request.args.get('clientId')
    interval = request.args.get('interval')
    specifiedDatetime = request.args.get('date') or ''

    try:
        clientId = int(clientId)
        if interval not in ['day', 'month', 'year']:
            return fail_response("interal must be one of the following: %s" % str(interval))
        dt = datetime.strptime(specifiedDatetime, "%Y-%m-%d")
    except ValueError as e:
        return fail_response("input error: %s" % str(e))


    # sql = """
    # SELECT dID, ET, {0}(CD), COUNT(*) FROM
    #     (SELECT d1.DeviceID AS dID,
    #         DeviceEvents.CreatedDate AS CD,
    #         DeviceEvents.EventType AS ET FROM
    #             (SELECT DISTINCT Device.DeviceID FROM Device
    #             INNER JOIN
    #             DeviceEvents
    #             ON Device.DeviceID = DeviceEvents.DeviceID
    #             WHERE Device.ClientID=%s)d1
    #             INNER JOIN
    #             DeviceEvents
    #             ON DeviceEvents.DeviceID = d1.DeviceID
    #             WHERE DeviceEvents.CreatedDate > %s
    #             AND DeviceEvents.CreatedDate < %s )d2
    #     GROUP BY dID, ET, {0}(CD);
    # """.format(interval.upper()) # use DAY(), MONTH(), or YEAR() SQL function

    sql = """
    SELECT d1.DeviceID AS dID,
            DeviceEvents.CreatedDate AS CD,
            DeviceEvents.EventType AS ET FROM
                (SELECT DISTINCT Device.DeviceID FROM Device
                  INNER JOIN
                    DeviceEvents
                  ON Device.DeviceID = DeviceEvents.DeviceID
                      WHERE Device.ClientID=%s)d1
                INNER JOIN
                DeviceEvents
                ON DeviceEvents.DeviceID = d1.DeviceID
                WHERE DeviceEvents.CreatedDate > %s
                AND DeviceEvents.CreatedDate < %s;
    """

    t_start = ""
    t_end = ""
    print(sql)

    # "%Y-%m-%d %H:%M:%S"
    # tb = datetime(dt.year, dt.month, dt.day, 0, 0, 0)

    buckets = {}

    if interval == 'day':
        t_start = str(specifiedDatetime) + " 00:00:00"
        t_end = str(specifiedDatetime) + " 23:59:59"

        params = (clientId, t_start, t_end)
        results = sql_select(sql, params)

        num_buckets = 48
        # create "buckets" every 30min so that when data is passed out
        # it can easily be processed by frontend chart code

        # drop results into buckets for count
        for row in results:
            deviceId, createdDate, eventType = row[0], row[1], row[2]

            if deviceId not in buckets:
                buckets[deviceId] = [0]*num_buckets

            minutes = createdDate.minute + (createdDate.hour*60)
            bucketLoc = int(math.floor(minutes / num_buckets))

            if eventType == 'entry':
                buckets[deviceId][bucketLoc] += 1

        return json.dumps(buckets)

    elif interval == 'month':
        t_start = datetime(dt.year, dt.month, 1)
        t_end = datetime(dt.year, dt.month+1, 1)

        params = (clientId, t_start, t_end)
        results = sql_select(sql, params)

        num_buckets = monthrange(dt.year, dt.month)[1]
        print(num_buckets)

        # drop results into buckets for count
        for row in results:
            deviceId, createdDate, eventType = row[0], row[1], row[2]

            if deviceId not in buckets:
                buckets[deviceId] = [0]*num_buckets

            days = createdDate.day-1
            bucketLoc = int(days)

            if eventType == 'entry':
                buckets[deviceId][bucketLoc] += 1

        return json.dumps(buckets)

    elif interval == 'year':
        t_start = datetime(dt.year, 1, 1)
        t_end = datetime(dt.year+1, 1, 1)
        # loop through months in that year

        params = (clientId, t_start, t_end)
        results = sql_select(sql, params)

        num_buckets = 12

        # drop results into buckets for count
        for row in results:
            deviceId, createdDate, eventType = row[0], row[1], row[2]

            if deviceId not in buckets:
                buckets[deviceId] = [0]*num_buckets

            months = createdDate.month-1
            bucketLoc = int(months)

            if eventType == 'entry':
                buckets[deviceId][bucketLoc] += 1

        return json.dumps(buckets)

    else:
        raise Exception("fail_response should have been issued for parameter interval")

    return ""


def get_buckets(results):
    """ Return buckets from the query results
        buckets: dictionary in the following format
        {
            1: [0,0,0,4,2,2,3,5,1,2,0,0],
            ...
        }
        where the key is the deviceId and the array
        is the volume of events in that interval
        """
    pass


@application.route('/AddDevice', methods=['POST'])
def AddDevice():
    """ parameters
        ------------------------
            deviceId :
            name :
            location :
            MACAddress :
    """

    deviceId = request.form.get('deviceId')
    name = request.form.get('name')
    location = request.form.get('location')
    MACAddress = request.form.get('MACAddress')

    try:
        deviceId = str(int(deviceId))
    except ValueError:
        return fail_response("device_id must be an integer")

    sql = """
    INSERT INTO Device (DeviceID, CreatedBy, ClientID, Name, MACAddress, Location)
    VALUES ( %s, 0, 1, %s, %s, %s );
    """

    try:
        params = (deviceId, name, MACAddress, location)
        sql_insert(sql, params)
    except Exception as e:
        return fail_response(e)

    return success_response()


@application.route('/AddUser', methods=['POST'])
def AddUser():
    """  INT clientId,
		STRING username,
		STRING firstName,
        STRING lastName,
        STRING email,
        STRING homePhone,
        STRING mobilePhone,
        STRING workPhone,
        STRING ext
         """
    clientId = request.form.get('clientId')
    username = request.form.get('username')
    firstName = request.form.get('firstName')
    lastName = request.form.get('lastName')
    email = request.form.get('email')
    homePhone = request.form.get('homePhone')
    mobilePhone = request.form.get('mobilePhone')
    workPhone = request.form.get('workPhone')
    ext = request.form.get('ext')

    try:
        clientId = str(int(clientId))
    except ValueError:
        return fail_response("clientId must be an integer")

    sql = """
    INSERT INTO Client
        (
        `ClientID`,
        `IndustryID`,
        `Name`,
        `Address1`,
        `Address2`,
        `City`,
        `State`,
        `ZipCode`,
        `ContactName`,
        `ContactEmail`,
        `ContactPhone`,
        `TimeZoneID`
        )
    VALUES ( %s, 0, '',);
    """

    try:
        params = (deviceId, name, MACAddress, location)
        sql_insert(sql, params)
    except Exception as e:
        return fail_response(e)

    return success_response()


@application.route('/GetBusinessHours', methods=['GET'])
def GetBusinessHours():
    """  """
    return ""


@application.route('/UpdateBusinessHours', methods=['POST'])
def UpdateBusinessHours():
    """  """
    return ""




# ENDPOINT TO AUTHENTICATE USERS




# @application.route('/GetCurrentOccupantsCount', methods=['GET'])
# def GetCurrentOccupantsCount():
#     """ Get the number of people in location on this day
#         (inCount - outCount) """
#     clientId = request.args['client_id']
#     today = datetime.utcnow().strftime("%Y-%m-%d")
#     today_start = today + " 00:00:00"
#     today_end = today + " 23:59:59"
#
#     sql = """
#     SELECT `DeviceEvents`.`EventType`
#     FROM `Device`
#     INNER JOIN `DeviceEvents`
#     ON `Device`.`DeviceID`=`DeviceEvents`.`DeviceID`
#       WHERE `Device`.`ClientID`=%s
#         AND `DeviceEvents`.`CreatedDate` > %s
#         AND `DeviceEvents`.`CreatedDate` < %s;
#     """
#
#     results = sql_select(sql, (clientId, today_start, today_end))
#     exit_count, entry_count, incrt_count = 0, 0, 0
#
#     for row in results:
#         eventType = row[0]
#         if eventType == 'entry':
#             entry_count += 1
#         elif eventType == 'exit':
#             exit_count += 1
#         else:
#             incrt_count += 1
#
#
#     num_people = entry_count - exit_count
#
#     success = 1
#     if num_people < 0:
#         success = 0
#
#     ret = {
#         'date': today,
#         'success' : success,
#         'num_people': num_people,
#         'entries': entry_count,
#         'exits': exit_count
#     }
#
#     return json.dumps(ret)


# @application.route('/GetDeviceStatus', methods=['GET'])
# def GetDeviceStatus(deviceId):
#     """ Get information about device/battery percent """
#     pass

# @application.route('/DeviceInBusinessHours', methods=['GET'])
# def DeviceInBusinessHours(deviceId):
#     """ Request to check if a device is in business hours
#         deviceId: int
#     """
#     pass
#     # reference device with associated client
#     # then check `ClientBusinessHours` table to see if device in business hours







######################
## Helper functions ##
######################

def sql_insert(sql_str, params=None):
    """ Helper function to run SQL SELECT query """
    creds = fetch_credentials()
    conn = None
    try:
        conn = mdb.connect(*creds) # unpack creds into params
        cursor = conn.cursor()
        cursor.execute(sql_str, params)
        conn.commit()
    except mdb.Error, e:
        err_str = "SQL INSERT Error %d: %s" % (e.args[0],e.args[1])
        print(err_str)
        raise Exception(err_str)
    finally:
        if conn:
            conn.close()


def sql_select(sql_str, params=None):
    """ Helper function to run SQL SELECT query """
    creds = fetch_credentials()
    conn = None
    results = []
    try:
        conn = mdb.connect(*creds) # unpack creds into params
        cursor = conn.cursor()
        cursor.execute(sql_str, params)
        results = cursor.fetchall()
    except mdb.Error, e:
        print("SQL SELECT Error %d: %s" % (e.args[0],e.args[1]))
        # TODO: THROW EXCEPTION
    finally:
        if conn:
            conn.close()
    # print("SQL results: %s" % (results, ))
    return results


def verify_token(t):
    """ Verify authorization token """
    # TODO: Complete authentication functionality
    return True


def fetch_credentials():
    """ Get SQL credentials from environment variables """
    return (os.environ['MYSQL_SERVER'],
            os.environ['MYSQL_USER'],
            os.environ['MYSQL_PASS'],
            os.environ['MYSQL_DB'])


def set_debug_db():
    """ Point db to local db if on debug """
    os.environ['MYSQL_SERVER'] = '127.0.0.1'
    os.environ['MYSQL_USER'] = 'root'
    os.environ['MYSQL_PASS'] = ''
    os.environ['MYSQL_DB'] = 'lidt'


if __name__ == "__main__":
    port_num = 80

    if len(sys.argv) > 1:
        if sys.argv[1] == '-debug':
            set_debug_db()
            port_num = 5000

    application.debug = True
    application.run(port=port_num)
