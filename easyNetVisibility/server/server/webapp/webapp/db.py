import mysql.connector

db_host = None
db_port = None
db_user = None
db_password = None
db_database = None


def init(param_db_host, param_db_port, param_db_user, param_db_passwd, param_db_database):
    global db_host
    global db_port
    global db_user
    global db_password
    global db_database

    db_host = param_db_host
    db_port = param_db_port
    db_user = param_db_user
    db_password = param_db_passwd
    db_database = param_db_database


def connect():
    db_connection = mysql.connector.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        passwd=db_password,
        database=db_database
    )

    return db_connection


# noinspection PyBroadException
def select(sql):
    db_connection = None
    cursor = None
    try:
        db_connection = connect()
        cursor = db_connection.cursor(dictionary=True)
        cursor.execute(sql)
        return cursor.fetchall()
    finally:
        try:
            if cursor is not None:
                cursor.close()
        except:
            pass
        try:
            if db_connection is not None:
                db_connection.close()
        except:
            pass


# noinspection PyBroadException
def update(sql, data):
    db_connection = None
    cursor = None
    try:
        db_connection = connect()
        cursor = db_connection.cursor(prepared=True)
        cursor.execute(sql, data)
        db_connection.commit()
    finally:
        try:
            db_connection.rollback()
        except:
            pass

        try:
            if cursor is not None:
                cursor.close()
        except:
            pass
        try:
            if db_connection is not None:
                db_connection.close()
        except:
            pass


def find_all_devices():
    return select("select devices.*, coalesce(device_ports.open_ports,0) as open_ports from devices left join (select device_id, count(*) as open_ports from ports group by device_id ) as device_ports on devices.device_id = device_ports.device_id")


def find_all_sensors():
    return select("SELECT * FROM sensors")


def find_sensor_by_mac(mac):
    return select("SELECT * FROM sensors where mac='" + mac + "'")


def find_sensor_by_sensor_id(sensor_id):
    return select("SELECT * FROM sensors where sensor_id=" + str(sensor_id))


def find_device_by_mac(mac):
    return select("SELECT * FROM devices where mac='" + mac + "'")


def find_device_by_device_id(device_id):
    return select("SELECT * FROM devices where device_id=" + str(device_id))


def find_ports_of_device(device_id):
    return select("SELECT * FROM ports where device_id=" + str(device_id))


def find_ports_by_device_and_num(device_id, port_num):
    return select("SELECT * FROM ports where device_id=" + str(device_id) + " and port_num=" + str(port_num))


def add_device(device_details):
    device_details_params = (
        device_details['hostname'],
        device_details['nickname'],
        device_details['ip'],
        device_details['mac'],
        device_details['vendor'],
        device_details['first_seen'],
        device_details['last_seen'])

    sql = """INSERT into devices(hostname,nickname,ip,mac,vendor,first_seen,last_seen) 
             values(%s,%s,%s,%s,%s,%s,%s) """

    update(sql, device_details_params)


def add_port(port_details):
    port_details_params = (
        port_details['device_id'],
        port_details['port_num'],
        port_details['protocol'],
        port_details['name'],
        port_details['product'],
        port_details['version'],
        port_details['first_seen'],
        port_details['last_seen'])

    sql = """INSERT INTO `ports`
                    (`device_id`,
                    `port_num`,
                    `protocol`,
                    `name`,
                    `product`,
                    `version`,
                    `first_seen`,
                    `last_seen`)
                    VALUES
                    (%s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s)
                    """

    update(sql, port_details_params)


def add_sensor(sensor_details):
    sensor_details_params = (
        sensor_details['mac'],
        sensor_details['hostname'],
        sensor_details['first_seen'],
        sensor_details['last_seen'])

    sql = """INSERT INTO `sensors` (
                            `mac`,
                            `hostname`,
                            `first_seen`,
                            `last_seen`)
                            VALUES
                    (%s,
                    %s,
                    %s,
                    %s)
                    """
    update(sql, sensor_details_params)


def update_sensor(sensor_details):
    sensor_details_params = (
        sensor_details['mac'],
        sensor_details['hostname'],
        sensor_details['first_seen'],
        sensor_details['last_seen'],
        sensor_details['sensor_id'])

    sql = """UPDATE `sensors` 
                            SET `mac`=%s,
                            `hostname`=%s,
                            `first_seen`=%s,
                            `last_seen`=%s
                            WHERE sensor_id=%s"""

    update(sql, sensor_details_params)


def update_port(port_details):
    port_details_params = (
        port_details['device_id'],
        port_details['port_num'],
        port_details['protocol'],
        port_details['name'],
        port_details['product'],
        port_details['version'],
        port_details['first_seen'],
        port_details['last_seen'],
        port_details['port_id'])

    sql = """UPDATE `ports`
                    SET device_id=%s,
                        port_num=%s,
                        protocol=%s,
                        name=%s,
                        product=%s,
                        version=%s,
                        first_seen=%s,
                        last_seen=%s
                    WHERE port_id=%s
                    """

    update(sql, port_details_params)


def update_device(device_details):
    device_details_params = (
        device_details['hostname'],
        device_details['nickname'],
        device_details['ip'],
        device_details['mac'],
        device_details['vendor'],
        device_details['first_seen'],
        device_details['last_seen'],
        device_details['device_id'])

    sql = """UPDATE devices set hostname=%s,nickname=%s,ip=%s,mac=%s,vendor=%s,first_seen=%s,
             last_seen=%s where device_id=%s"""

    update(sql, device_details_params)


def delete_device(device_id):
    update("""DELETE from devices where device_id=%s""", str(device_id))


def delete_sensor(sensor_id):
    update("""DELETE from sensors where sensor_id=%s""", str(sensor_id))
