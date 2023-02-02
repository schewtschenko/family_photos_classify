import sys
import os
import psycopg2
from famphoto.BaseConfig import BaseConfig
from famphoto.gpsphoto import GPSPhoto


def _select_unproc_gnss_images(conn, limit_num):
    '''
    Returns (success, dict {image_id, image_path})

    subfold_filter,

    stmt = ('select'
            '  im.id,'
            '  concat_ws(\'/\', fld.name, im.file_name) as image_path'
            ' from'
            '  subfolder fld,'
            '  image im left outer join image_location imloc'
            '   on im.id = imloc.image_id'
            ' where'
            '  (fld.name like %s)'
            '  and (im.subfolder_id = fld.id)'
            '  and (imloc.image_id is NULL)'
            ' limit %s')
    '''
    stmt = ('select'
            '  im.id,'
            '  concat_ws(\'/\', fld.name, im.file_name) as image_path'
            ' from'
            '  subfolder fld,'
            '  image im left outer join image_location imloc'
            '   on im.id = imloc.image_id'
            ' where'
            '  (im.subfolder_id = fld.id)'
            '  and (imloc.image_id is NULL)'
            ' limit %s')
    cursor = None
    images_tab = {}
    success = True
    try:
        cursor = conn.cursor()
        #cursor.execute(stmt, (subfold_filter, limit_num))
        cursor.execute(stmt, (limit_num, ))
        for record in cursor:
            if record:
                image_id = int(record[0])
                image_path = str(record[1])
                images_tab[image_id] = image_path
    except psycopg2.Error as err:
        print(err.pgerror, file=sys.stderr)
        success = False
    finally:
        if cursor:
            cursor.close()

    return (success, images_tab)


def _insert_image_location_ref(conn, image_id, location_id, has_gnss, lat, lon):
    '''
    Returns boolean
    '''
    stmt = ('insert into image_location (image_id, location_id, gnss_pos, latitude, longitude)'
            ' values (%s, %s, %s, %s, %s)')
    cursor = None
    success = True
    if has_gnss:
        gnss_pos = 'Y'
        latitude = float(lat)
        longitude = float(lon)
    else:
        gnss_pos = 'N'
        latitude = 0.0
        longitude = 0.0

    try:
        cursor = conn.cursor()
        cursor.execute(stmt, (image_id, location_id,
                       gnss_pos, latitude, longitude))
    except psycopg2.Error as err:
        print(err.pgerror, file=sys.stderr)
        success = False
    finally:
        if cursor:
            cursor.close()
    return success


class ExtractGnssData(BaseConfig):
    def __init__(self):
        super().__init__()

    def extract_gnss_data(self, limit_num):
        base_folder = self.get_base_folder()
        (success, images_tab) = _select_unproc_gnss_images(
            self.conn, limit_num)
        counter = 0
        if success:
            for image_id, image_rel_path in images_tab.items():
                image_path = os.path.join(base_folder, image_rel_path)
                if not os.path.exists(image_path):
                    print(f'error: image path does not exist: {image_path}')
                    continue
                try:
                    gphoto = GPSPhoto(image_path)
                    gdata = gphoto.getGPSData()
                    if 'Latitude' in gdata and 'Longitude' in gdata:
                        print('+', end='', flush=True)
                        success = _insert_image_location_ref(
                            self.conn, image_id, 0, True, gdata['Latitude'], gdata['Longitude'])
                    else:
                        print('0', end='', flush=True)
                        success = _insert_image_location_ref(
                            self.conn, image_id, 0, False, None, None)
                except ValueError as err:
                    print(f'error: {err}', file=sys.stderr)
                    success = False
                if success:
                    self.conn.commit()
                else:
                    self.conn.rollback()
                counter += 1
                if counter % 80 == 0:
                    print()
