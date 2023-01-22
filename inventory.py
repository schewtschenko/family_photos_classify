import sys
import os
from famphoto.AddNewImages import AddNewImages

def main():
    if len(sys.argv) < 2:
        print('usage: {} <path_to_config>'.format(sys.argv[0]))
        sys.exit(1)

    config_path = sys.argv[1]
    if not os.path.isfile(config_path):
        print('error: not a file "{}"'.format(config_path))
        sys.exit(1)

    exclude_folder_names = ['_import', '.@__thumb', '_damaged']

    inventory = AddNewImages()

    inventory.initialize(config_path)
    inventory.enumerate_image_files(exclude_folder_names)
    inventory.store_logs()
    inventory.cleanup()


if __name__ == '__main__':
    main()
