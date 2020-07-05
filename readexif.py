import sys
import os
from PIL import Image
from PIL.ExifTags import TAGS
from PIL.ExifTags import GPSTAGS

tag_names = {'ExifImageWidth', 'ExifImageHeight',
             'DateTime', 'DateTimeDigitized', 'DateTimeOriginal', 'Model', 'GPSInfo'}


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
                # extract EXIF data
                exif_data = image_data.getexif()
                # iterating over all EXIF data fields
                for tag_id in exif_data:
                    # get the tag name, instead of human unreadable tag id
                    tag_name = str(TAGS.get(tag_id, tag_id))
                    if tag_name in tag_names:
                        val = exif_data.get(tag_id)
                        print('  {:20} {}'.format(tag_name, str(val)))


if __name__ == '__main__':
    main()
