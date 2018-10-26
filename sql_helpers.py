import MySQLdb as mdb
from helpers import fetch_credentials


def sql_insert(sql_str, params=None):
    """ Helper function to run SQL SELECT query """
    creds, conn = fetch_credentials(), None

    try:
        conn = mdb.connect(*creds)  # unpack creds into params
        cursor = conn.cursor()
        cursor.execute(sql_str, params)
        conn.commit()

    except mdb.Error as e:
        err_str = "SQL INSERT Error %d: %s" % (e.args[0], e.args[1])
        raise Exception(err_str)

    finally:
        if conn:
            conn.close()


def sql_select(sql_str, params=None):
    """ Helper function to run SQL SELECT query """
    creds, conn, results = fetch_credentials(), None, []

    try:
        conn = mdb.connect(*creds)  # unpack creds into params
        cursor = conn.cursor()
        cursor.execute(sql_str, params)
        results = cursor.fetchall()

    except mdb.Error as e:
        err_str = "SQL SELECT Error %d: %s" % (e.args[0], e.args[1])
        raise Exception(err_str)

    finally:
        if conn:
            conn.close()

    return results
