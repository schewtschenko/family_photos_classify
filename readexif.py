import sys
import os
from PIL import Image
from PIL.ExifTags import TAGS
from PIL.ExifTags import GPSTAGS

processed_tag_names = {'ExifImageWidth', 'ExifImageHeight',
                       'DateTime', 'DateTimeOriginal',
                       'Model', 'GPSInfo'}


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


def process_gps_info(gps_info, props):
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


def process_exif(exif_data, tag_names, props):
    if not exif_data:
        return
    # iterating over tags will work
    for tag_id in exif_data:
        if tag_id in TAGS:
            tag_name = TAGS[tag_id]
            if tag_name in tag_names:
                value = exif_data.get(tag_id)
                if tag_name == 'GPSInfo':
                    process_gps_info(value, props)
                else:
                    props[tag_name] = value


def main():
    if len(sys.argv) < 2:
        print('error: few arguments')
        sys.exit(1)

    images_dir = sys.argv[1]
    if not os.path.isdir(images_dir):
        print('error: not a folder "{}"'.format(images_dir))
        sys.exit(1)

    # enumerate files
    for file_name in os.listdir(images_dir):
        file_path = os.path.join(images_dir, file_name)
        if os.path.isfile(file_path):
            _, file_ext = os.path.splitext(file_name)
            if file_ext.lower() == '.jpg':
                print('---------- {} ----------'.format(file_name))
                # read the image data using PIL
                image_data = Image.open(file_path)
                # extract and process EXIF data
                exif_props = {}
                exif_data = image_data.getexif()
                process_exif(exif_data, processed_tag_names, exif_props)
                # check
                if 'GPSLatitude' in exif_props and 'GPSLongitude' in exif_props:
                    print('{}, {}'.format(exif_props['GPSLatitude'], exif_props['GPSLongitude']))


'''
orig_image = cv2.imread(file_path)
orig_height, orig_width, _ = orig_image.shape
bgr_image = cv2.imread(file_path)
if bgr_image.size > 1:
    next_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
image=PIL.Image.fromarray(self.cv_image)
'''

if __name__ == '__main__':
    main()
