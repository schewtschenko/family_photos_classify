import sys
import os
import yaml
import mysql.connector
from PIL import Image
from PIL.ExifTags import TAGS
from PIL.ExifTags import GPSTAGS
from datetime import datetime


def check_config_root_folder(config_data):
    if not 'root_folder' in config_data:
        return False
    folders_list = config_data['root_folder']
    folders_count = 0
    for folder in folders_list:
        if os.path.isdir(folder):
            folders_count += 1
            print('info: use data from "{}"'.format(folder))
        else:
            print('warning: not a folder "{}"'.format(folder))
    if folders_count > 0 and folders_count == len(folders_list):
        return True
    else:
        return False


def check_config_db_connect(config_data):
    if not 'db_connect' in config_data:
        return False
    props = config_data['db_connect']
    for prop_name in ['user', 'password', 'host', 'database']:
        if not prop_name in props:
            print('error: incomplete DB connection info "{}" is not specified'.format(
                prop_name))
            return False
    return True


def make_db_connection(config_data):
    conn_obj = None
    try:
        conn_props = config_data['db_connect']
        conn_obj = mysql.connector.connect(user=conn_props['user'], password=conn_props['password'],
                                           host=conn_props['host'], database=conn_props['database'],
                                           autocommit=False,
                                           charset='utf8', collation='utf8_general_ci')
    except mysql.connector.Error as err:
        print(err)
    return conn_obj


def get_root_folder_list(config_data):
    return config_data['root_folder']


processed_tag_names = {'ExifImageWidth', 'ExifImageHeight',
                       'DateTime', 'DateTimeOriginal', 'DateTimeDigitized',
                       'Make', 'Model', 'GPSInfo'}


def convert_to_decimal_degrees(value):
    # it seems the value is stored in the following way:
    #  ((degrees, divider), (minutes, divider), (seconds, divider))
    #  ((45, 1), (21, 1), (89980, 10000))
    d0 = value[0][0]
    d1 = value[0][1]
    d = float(d0) / float(d1)
    m0 = value[1][0]
    m1 = value[1][1]
    m = float(m0) / float(m1)
    s0 = value[2][0]
    s1 = value[2][1]
    s = float(s0) / float(s1)
    return d + (m / 60.0) + (s / 3600.0)


def read_gps_info(gps_info, props):
    # gps_info may contain the following data:
    #  {1: 'N', 2: ((45, 1), (21, 1), (89980, 10000)),
    #   3: 'E', 4: ((32, 1), (55, 1), (535950, 10000)),
    #   5: b'\x00', 6: (27412, 1000), 7: ((15, 1), (7, 1), (58, 1)),
    #   27: 'ASCII\x00\x00\x00GPS', 29: '2019:07:18'}
    if not isinstance(gps_info, dict):
        return
    gps_lat = None
    gps_lat_ref = None
    gps_lon = None
    gps_lon_ref = None
    for tag_id, val in gps_info.items():
        if tag_id in GPSTAGS:
            tag_name = GPSTAGS[tag_id]
            if tag_name == 'GPSLatitude':
                gps_lat = val
            elif tag_name == 'GPSLatitudeRef':
                gps_lat_ref = val
            elif tag_name == 'GPSLongitude':
                gps_lon = val
            elif tag_name == 'GPSLongitudeRef':
                gps_lon_ref = val
    # latitude
    if gps_lat and gps_lat_ref:
        lat = convert_to_decimal_degrees(gps_lat)
        if gps_lat_ref == 'S':
            lat = -lat
        props['GPSLatitude'] = lat
    # longitude
    if gps_lon and gps_lon_ref:
        lon = convert_to_decimal_degrees(gps_lon)
        if gps_lon_ref == 'W':
            lon = -lon
        props['GPSLongitude'] = lon


def read_image_exif(exif_data, tag_names):
    image_props = {}
    if exif_data:
        # iterating over tags will work
        for tag_id in exif_data:
            if tag_id in TAGS:
                tag_name = TAGS[tag_id]
                if tag_name in tag_names:
                    value = exif_data.get(tag_id)
                    if tag_name == 'GPSInfo':
                        read_gps_info(value, image_props)
                    else:
                        if isinstance(value, str):
                            # remove '\x00' at right
                            value = value.rstrip('\x00')
                            # remove begin and end spaces
                            value = value.strip()
                            # do not put empty strings
                            if len(value) == 0:
                                continue
                        image_props[tag_name] = value
    return image_props


def read_image_props(file_path):
    # read the image data using PIL
    image_data = Image.open(file_path)
    # extract and process EXIF data
    exif_data = image_data.getexif()
    image_props = read_image_exif(exif_data, processed_tag_names)
    image_width, image_height = image_data.size
    image_props['ResWidth'] = image_width
    image_props['ResHeight'] = image_height
    return image_props


def select_subfolder_id(conn, subfolder):
    '''
    Returns (error_num, has_data, subfolder_id)
    '''
    stmt = 'SELECT id FROM subfolder WHERE name = %s'
    cursor = None
    (error_num, has_data, subfolder_id) = (0, False, 0)
    try:
        cursor = conn.cursor()
        cursor.execute(stmt, (subfolder,))
        record = cursor.fetchone()
        if record:
            subfolder_id = int(record[0])
            has_data = True
    except mysql.connector.Error as err:
        print(err)
        error_num = err.errno
    finally:
        if cursor:
            cursor.close()
    return (error_num, has_data, subfolder_id)


def insert_subfolder_get_id(conn, subfolder):
    '''
    Returns (error_num, subfolder_id)
    '''
    stmt_select = 'SELECT MAX(id) FROM subfolder'
    stmt_insert = 'INSERT INTO subfolder (id, name) VALUES (%s, %s)'
    cursor_select = None
    cursor_insert = None
    (error_num, subfolder_id) = (0, 0)
    try:
        cursor_select = conn.cursor()
        cursor_select.execute(stmt_select)
        record = cursor_select.fetchone()
        if record[0]:
            subfolder_id = int(record[0]) + 1
        else:
            subfolder_id = 1
        cursor_insert = conn.cursor()
        cursor_insert.execute(stmt_insert, (subfolder_id, subfolder))
    except mysql.connector.Error as err:
        print(err)
        error_num = err.errno
    finally:
        if cursor_select:
            cursor_select.close()
        if cursor_insert:
            cursor_insert.close()
    return (error_num, subfolder_id)


def select_camera_id(conn, model):
    '''
    Returns (error_num, has_data, camera_id)
    '''
    stmt = 'SELECT id FROM camera WHERE model = %s'
    cursor = None
    (error_num, has_data, camera_id) = (0, False, 0)
    try:
        cursor = conn.cursor()
        cursor.execute(stmt, (model,))
        record = cursor.fetchone()
        if record:
            camera_id = int(record[0])
            has_data = True
    except mysql.connector.Error as err:
        print(err)
        error_num = err.errno
    finally:
        if cursor:
            cursor.close()
    return (error_num, has_data, camera_id)


def insert_camera_get_id(conn, model, brand):
    '''
    Returns (error_num, camera_id)
    '''
    stmt_select = 'SELECT MAX(id) FROM camera'
    stmt_insert = 'INSERT INTO camera (id, model, brand) VALUES (%s, %s, %s)'
    cursor_select = None
    cursor_insert = None
    (error_num, camera_id) = (0, 0)
    try:
        cursor_select = conn.cursor()
        cursor_select.execute(stmt_select)
        record = cursor_select.fetchone()
        if record[0]:
            camera_id = int(record[0]) + 1
        else:
            camera_id = 1
        cursor_insert = conn.cursor()
        cursor_insert.execute(stmt_insert, (camera_id, model, brand))
    except mysql.connector.Error as err:
        print(err)
        print(len(model), ' -> ', list(model))
        print(brand)
        error_num = err.errno
    finally:
        if cursor_select:
            cursor_select.close()
        if cursor_insert:
            cursor_insert.close()
    return (error_num, camera_id)


def select_image_id(conn, file_name, subfolder_id):
    '''
    Returns (error_num, has_data, image_id)
    '''
    stmt = 'SELECT id FROM image WHERE file_name = %s AND subfolder_id = %s'
    cursor = None
    (error_num, has_data, image_id) = (0, False, 0)
    try:
        cursor = conn.cursor()
        cursor.execute(stmt, (file_name, subfolder_id))
        record = cursor.fetchone()
        if record:
            image_id = int(record[0])
            has_data = True
    except mysql.connector.Error as err:
        print(err)
        error_num = err.errno
    finally:
        if cursor:
            cursor.close()
    return (error_num, has_data, image_id)


def insert_image_get_id(conn, file_name, subfolder_id, res_width, res_height, camera_id, photo_time):
    '''
    Returns (error_num, image_id)
    '''
    stmt_select = 'SELECT MAX(id) FROM image'
    # TODO reformat the long string
    stmt_insert = 'INSERT INTO image (id, file_name, subfolder_id, resolution_width, resolution_height, camera_id, photo_time) VALUES (%s, %s, %s, %s, %s, %s, %s)'
    cursor_select = None
    cursor_insert = None
    (error_num, image_id) = (0, 0)
    try:
        cursor_select = conn.cursor()
        cursor_select.execute(stmt_select)
        record = cursor_select.fetchone()
        if record[0]:
            image_id = int(record[0]) + 1
        else:
            # special case for empty 'image' table
            image_id = 1
        cursor_insert = conn.cursor()
        cursor_insert.execute(stmt_insert, (image_id, file_name,
                                            subfolder_id, res_width, res_height, camera_id, photo_time))
    except mysql.connector.Error as err:
        print(err)
        error_num = err.errno
    finally:
        if cursor_select:
            cursor_select.close()
        if cursor_insert:
            cursor_insert.close()
    return (error_num, image_id)


def fix_extra_spaces(exif_datetime):
    '''
    sometimes input looks like:
    '2015: 8:21 11:31: 7'
     0123456789012345678
    '''
    if exif_datetime.count(' ') > 1:
        if len(exif_datetime) == 19:
            chars = list(exif_datetime)
            for i in [5, 8, 11, 14, 17]:
                if chars[i] == ' ':
                    chars[i] = '0'
            return ''.join(chars)
    return exif_datetime


def check_and_convert_datetime(exif_datetime):
    '''
    Input   Exif: '2020:01:06 16:01:06'
    Output MySql: 'YYYY-MM-DD hh:mm:ss'
    '''
    if not exif_datetime:
        return None
    fixed_datetime = fix_extra_spaces(exif_datetime)
    mysql_datetime = None
    try:
        dt = datetime.strptime(fixed_datetime, '%Y:%m:%d %H:%M:%S')
        mysql_datetime = dt.strftime('%Y-%m-%d %H:%M:%S')
    except ValueError as err:
        print(err)
    return mysql_datetime


def lookup_image(conn, file_name, subfolder):
    pass


def insert_gps_location(conn, image_id, lat, lon):
    '''
    Returns error_num
    '''
    stmt = 'INSERT INTO gps_location (image_id, latitude, longitude) VALUES (%s, %s, %s)'
    cursor = None
    error_num = 0
    try:
        cursor = conn.cursor()
        cursor.execute(stmt, (image_id, lat, lon))
    except mysql.connector.Error as err:
        print(err)
        error_num = err.errno
    finally:
        if cursor:
            cursor.close()
    return error_num


def test_gps_location(conn, image_id):
    '''
    Returns (error_num, has_data)
    '''
    stmt = 'SELECT COUNT(image_id) FROM gps_location WHERE image_id = %s'
    cursor = None
    (error_num, has_data) = (0, False)
    try:
        cursor = conn.cursor()
        cursor.execute(stmt, (image_id,))
        record = cursor.fetchone()
        if int(record[0]) > 0:
            has_data = True
    except mysql.connector.Error as err:
        print(err)
        error_num = err.errno
    finally:
        if cursor:
            cursor.close()
    return (error_num, has_data)


def register_gps_location(conn, image_id, image_props):
    if 'GPSLatitude' in image_props and 'GPSLongitude' in image_props:
        (error_num, has_data) = test_gps_location(conn, image_id)
        if error_num == 0 and not has_data:
            lat = float(image_props['GPSLatitude'])
            lon = float(image_props['GPSLongitude'])
            error_num = insert_gps_location(conn, image_id, lat, lon)


def register_image(conn, file_name, subfolder, image_props):
    # subfolder
    (error_num, has_data, subfolder_id) = select_subfolder_id(conn, subfolder)
    if error_num == 0 and not has_data:
        (error_num, subfolder_id) = insert_subfolder_get_id(conn, subfolder)
    if error_num != 0:
        return False
    # camera
    camera_model = image_props.get('Model', None)
    if camera_model:
        error_num, has_data, camera_id = select_camera_id(conn, camera_model)
        if error_num == 0 and not has_data:
            camera_brand = image_props.get('Make', None)
            (error_num, camera_id) = insert_camera_get_id(
                conn, camera_model, camera_brand)
        if error_num != 0:
            print('error:', subfolder, file_name)
            return False
    else:
        camera_id = 0
    # image size
    image_width = int(image_props['ResWidth'])
    image_height = int(image_props['ResHeight'])
    if 'ExifImageWidth' in image_props and 'ExifImageHeight' in image_props:
        exif_width = image_props['ExifImageWidth']
        exif_height = image_props['ExifImageHeight']
        if isinstance(exif_width, int) and isinstance(exif_height, int):
            if exif_width != image_width or exif_height != image_height:
                print('warning: mismatch of image sizes: {} and {} for {}/{}'.format(
                    (image_width, image_height), (exif_width, exif_height), subfolder, file_name))
    # image datetime
    photo_datetime = check_and_convert_datetime(
        image_props.get('DateTime', None))
    if not photo_datetime:
        photo_datetime = check_and_convert_datetime(
            image_props.get('DateTimeOriginal', None))
    if not photo_datetime:
        photo_datetime = check_and_convert_datetime(
            image_props.get('DateTimeDigitized', None))
    # image
    (error_num, has_data, image_id) = select_image_id(
        conn, file_name, subfolder_id)
    if error_num == 0 and not has_data:
        # add new image
        (error_num, image_id) = insert_image_get_id(conn, file_name,
                                                    subfolder_id, image_width, image_height, camera_id, photo_datetime)
        if error_num == 0:
            register_gps_location(conn, image_id, image_props)
            conn.commit()
            # print('info: added image {}, id={}'.format(file_name, image_id))
        else:
            conn.rollback()


def enumerate_image_files(root_folder, conn, **kwargs):
    max_count = kwargs.get('max_count', 0)
    file_count = 0
    root_folder_len = len(root_folder)
    for immediate_folder, _, files in os.walk(root_folder, topdown=False, followlinks=False):
        immediate_folder_len = len(immediate_folder)
        for file_name in files:
            # only JPEG files
            _, file_ext = os.path.splitext(file_name)
            if file_ext.lower() in ['.jpg', '.jpeg']:
                # read image properties
                file_path = os.path.join(immediate_folder, file_name)
                image_props = read_image_props(file_path)
                if immediate_folder_len > root_folder_len:
                    subfolder = immediate_folder[len(root_folder) + 1:]
                else:
                    subfolder = '.'

                register_image(conn, file_name, subfolder, image_props)

                file_count += 1
                if max_count > 0 and file_count >= max_count:
                    return


def main():
    if len(sys.argv) < 2:
        print('usage: {} <path_to_config>'.format(sys.argv[0]))
        sys.exit(1)

    config_path = sys.argv[1]
    if not os.path.isfile(config_path):
        print('error: not a file "{}"'.format(config_path))
        sys.exit(1)

    config_data = None
    with open(config_path, 'r') as config_stream:
        config_data = yaml.load(config_stream, Loader=yaml.FullLoader)

    if not check_config_root_folder(config_data):
        sys.exit(1)
    if not check_config_db_connect(config_data):
        sys.exit(1)

    # connect to db
    conn = make_db_connection(config_data)
    if not conn:
        sys.exit(1)
    # for each data folder
    for folder in get_root_folder_list(config_data):
        # enumerate JPEG images
        enumerate_image_files(folder, conn)
        #enumerate_image_files(folder, conn)
    # close db connection
    conn.close()


if __name__ == '__main__':
    main()
