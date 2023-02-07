#import sys
#import os
import json
from famphoto.BaseConfig import BaseConfig


def _select_image_locations(conn):
    stmt = ('select imloc.image_id, imloc.latitude, imloc.longitude'
            ' from image_location imloc'
            ' where imloc.gnss_pos = \'Y\'')
    imlocs = []
    with conn.cursor() as cursor:
        cursor.execute(stmt)
        for record in cursor:
            if record:
                image_id = int(record[0])
                lat = float(record[1])
                lon = float(record[2])
                imlocs.append((image_id, lat, lon))
    return imlocs


class ImageLocations(BaseConfig):
    def __init__(self):
        super().__init__()

    def load_image_locations(self):
        imlocs = _select_image_locations(self.conn)
        return imlocs


def main():
    il = ImageLocations()
    if il.initialize('configs/newconfig.yaml'):
        imlocs = il.load_image_locations()
        if imlocs:
            print(f'number of locations: {len(imlocs)}')
            with open('dumps/imlocs.json', 'w') as file_stream:
                json.dump(imlocs, file_stream)
    il.cleanup()


if __name__ == '__main__':
    main()
