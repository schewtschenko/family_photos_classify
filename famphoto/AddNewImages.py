from PIL import Image
from PIL.ExifTags import TAGS
import sys
import os
import psycopg2
from datetime import datetime
import yaml
from famphoto.BaseImageEnum import BaseImageEnum


def _select_subfolder_id(conn, subfolder):
    '''
    Returns (success, has_data, subfolder_id)
    '''
    stmt = 'SELECT id FROM subfolder WHERE name = %s'
    cursor = None
    (success, has_data, subfolder_id) = (True, False, 0)
    try:
        cursor = conn.cursor()
        cursor.execute(stmt, (subfolder,))
        record = cursor.fetchone()
        if record:
            subfolder_id = int(record[0])
            has_data = True
    except psycopg2.Error as err:
        print(err.pgerror, file=sys.stderr)
        success = False
    finally:
        if cursor:
            cursor.close()
    return (success, has_data, subfolder_id)


def _insert_subfolder_get_id(conn, subfolder):
    '''
    Returns (success, subfolder_id)
    '''
    stmt_select = 'SELECT MAX(id) FROM subfolder'
    stmt_insert = 'INSERT INTO subfolder (id, name) VALUES (%s, %s)'
    cursor_select = None
    cursor_insert = None
    (success, subfolder_id) = (True, 0)
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
    except psycopg2.Error as err:
        print(err.pgerror, file=sys.stderr)
        success = False
    finally:
        if cursor_select:
            cursor_select.close()
        if cursor_insert:
            cursor_insert.close()
    return (success, subfolder_id)


def _select_image_id(conn, file_name, subfolder_id):
    '''
    Returns (success, has_data, image_id)
    '''
    stmt = 'SELECT id FROM image WHERE file_name = %s AND subfolder_id = %s'
    cursor = None
    (success, has_data, image_id) = (True, False, 0)
    try:
        cursor = conn.cursor()
        cursor.execute(stmt, (file_name, subfolder_id))
        record = cursor.fetchone()
        if record:
            image_id = int(record[0])
            has_data = True
    except psycopg2.Error as err:
        print(err.pgerror, file=sys.stderr)
        success = False
    finally:
        if cursor:
            cursor.close()
    return (success, has_data, image_id)


def _select_camera_id(conn, model):
    '''
    Returns (success, has_data, camera_id)
    '''
    stmt = 'SELECT id FROM camera WHERE model = %s'
    cursor = None
    (success, has_data, camera_id) = (True, False, 0)
    try:
        cursor = conn.cursor()
        cursor.execute(stmt, (model,))
        record = cursor.fetchone()
        if record:
            camera_id = int(record[0])
            has_data = True
    except psycopg2.Error as err:
        print(err.pgerror, file=sys.stderr)
        success = False
    finally:
        if cursor:
            cursor.close()
    return (success, has_data, camera_id)


def _insert_camera_get_id(conn, model, brand):
    '''
    Returns (success, camera_id)
    '''
    stmt_select = 'SELECT MAX(id) FROM camera'
    stmt_insert = 'INSERT INTO camera (id, model, brand) VALUES (%s, %s, %s)'
    cursor_select = None
    cursor_insert = None
    (success, camera_id) = (True, 0)
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
    except psycopg2.Error as err:
        print(err.pgerror, file=sys.stderr)
        success = False
    finally:
        if cursor_select:
            cursor_select.close()
        if cursor_insert:
            cursor_insert.close()
    return (success, camera_id)


def _register_camera(conn, image_props):
    '''
    Returns (success, has_data, camera_id)
    '''
    (success, has_data, camera_id) = (True, False, 0)
    camera_model = image_props.get('Model', None)
    if camera_model:
        (success, has_data, camera_id) = _select_camera_id(conn, camera_model)
        if success and not has_data:
            camera_brand = image_props.get('Make', None)
            (success, camera_id) = _insert_camera_get_id(
                conn, camera_model, camera_brand)
            if success:
                has_data = True
            else:
                print(
                    f'error: unable to register camera: {camera_model}', file=sys.stderr)
                has_data = False
                camera_id = 0
    else:
        # no camera information
        (success, has_data, camera_id) = (True, True, 0)

    return (success, has_data, camera_id)


def _fix_extra_spaces(exif_datetime):
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


def _check_and_convert_datetime(exif_datetime):
    '''
    Input  Exif: '2020:01:06 16:01:06'
    Output   DB: 'YYYY-MM-DD hh:mm:ss'
    '''
    if not exif_datetime:
        return None
    fixed_datetime = _fix_extra_spaces(exif_datetime)
    iso8601_datetime = None
    try:
        dt = datetime.strptime(fixed_datetime, '%Y:%m:%d %H:%M:%S')
        iso8601_datetime = dt.strftime('%Y-%m-%d %H:%M:%S')
    except ValueError as err:
        print(err, file=sys.stderr)
    return iso8601_datetime


def _insert_image_get_id(conn, file_name, subfolder_id, res_width, res_height, camera_id, photo_time):
    '''
    Returns (success, image_id)
    '''
    stmt_select = 'SELECT MAX(id) FROM image'
    # TODO reformat the long string
    stmt_insert = 'INSERT INTO image (id, file_name, subfolder_id, res_width, res_height, camera_id, photo_time) VALUES (%s, %s, %s, %s, %s, %s, %s)'
    cursor_select = None
    cursor_insert = None
    (success, image_id) = (True, 0)
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
    except psycopg2.Error as err:
        print(err.pgerror, file=sys.stderr)
        success = False
    finally:
        if cursor_select:
            cursor_select.close()
        if cursor_insert:
            cursor_insert.close()
    return (success, image_id)


def _register_image(conn, image_props, file_name, subfolder_id):
    registered = False
    if 'width' in image_props and 'height' in image_props:
        # image size
        image_width = int(image_props['width'])
        image_height = int(image_props['height'])
        # camera
        (success, has_data, camera_id) = _register_camera(conn, image_props)
        if success and has_data:
            # image datetime
            photo_datetime = _check_and_convert_datetime(
                image_props.get('DateTime', None))
            if not photo_datetime:
                photo_datetime = _check_and_convert_datetime(
                    image_props.get('DateTimeOriginal', None))
            if not photo_datetime:
                photo_datetime = _check_and_convert_datetime(
                    image_props.get('DateTimeDigitized', None))

            # add new image
            (success, image_id) = _insert_image_get_id(conn, file_name,
                                                        subfolder_id,
                                                        image_width, image_height,
                                                        camera_id, photo_datetime)
            if success:
                registered = True
            else:
                print(
                    f'warning: unable to insert image: {file_name}', file=sys.stderr)
        else:
            print(
                f'warning: unable to register camera: {file_name}', file=sys.stderr)
    else:
        print(f'warning: no size: {file_name}', file=sys.stderr)

    if registered:
        conn.commit()
    else:
        conn.rollback()

    return registered


def _extract_exif(exif_data, tag_names, props):
    if exif_data:
        # iterating over tags will work
        for tag_id in exif_data:
            if tag_id in TAGS:
                tag_name = TAGS[tag_id]
                if tag_name in tag_names:
                    value = exif_data.get(tag_id)
                    if isinstance(value, str):
                        # remove '\x00' at right
                        value = value.rstrip('\x00')
                        # remove begin and end spaces
                        value = value.strip()
                        # do not put empty strings
                        if len(value) == 0:
                            continue
                    props[tag_name] = value


tag_names = {'ExifImageWidth', 'ExifImageHeight',
             'DateTime', 'DateTimeOriginal', 'DateTimeDigitized',
             'Make', 'Model'}


class AddNewImages(BaseImageEnum):
    def __init__(self):
        super().__init__()
        self.exist_images_count = 0
        self.new_images_count = 0
        self.added_subfolders_count = 0
        self.added_images_count = 0
        self.damaged_images_tab = {}

    def read_image_props(self, image_path, image_props):
        valid = True
        try:
            with Image.open(image_path) as imdata:
                image_width, image_height = imdata.size
                image_props['width'] = image_width
                image_props['height'] = image_height
                _extract_exif(imdata.getexif(), tag_names, image_props)
        except OSError as err:
            print(f'error: {err}', file=sys.stderr)
            valid = False
        return valid

    def handle_image_file(self, image_path, image_name, subfolder):
        registered = False
        improps = {}
        valid = True
        # check for subfolder
        (success, has_data, subfolder_id) = _select_subfolder_id(
            self.conn, subfolder)
        if success and has_data:
            # subfolder is present, check for image
            (success, has_data, image_id) = _select_image_id(
                self.conn, image_name, subfolder_id)
            if success and has_data:
                # image is present
                self.exist_images_count += 1
            else:
                # image is not registered
                self.new_images_count += 1
                valid = self.read_image_props(image_path, improps)
                if valid:
                    registered = _register_image(
                        self.conn, improps, image_name, subfolder_id)
        else:
            # no subfolder - no image
            self.new_images_count += 1
            (success, subfolder_id) = _insert_subfolder_get_id(
                self.conn, subfolder)
            if success:
                valid = self.read_image_props(image_path, improps)
                if valid:
                    registered = _register_image(
                        self.conn, improps, image_name, subfolder_id)
                    if registered:
                        self.added_subfolders_count += 1
        if registered:
            self.added_images_count += 1
        if not valid:
            self.damaged_images_tab[image_path] = os.path.join(
                self.get_base_folder(), '_damaged', subfolder, image_name)

    def store_logs(self):
        # print summary
        print()
        print(f'info: images exist={self.exist_images_count}',
              file=sys.stderr)
        print(f'info: images   new={self.new_images_count}',
              file=sys.stderr)
        print(f'info: images added={self.added_images_count}',
              file=sys.stderr)
        print(f'info: folders added={self.added_subfolders_count}',
              file=sys.stderr)
        # dump damaged images
        if self.damaged_images_tab:
            yaml.dump(self.damaged_images_tab, sys.stderr)
            #curlog_path = datetime.now().strftime('logs/damaged_%y%m%d_%H%M%S.yaml')
            #with open(curlog_path, 'w') as curlog_stream:
            #    yaml.dump(self.damaged_images_tab, curlog_stream)
