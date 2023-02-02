import os
import sys
from famphoto.ExtractGnssData import ExtractGnssData

def main():
    if len(sys.argv) < 2:
        print('usage: {} <path_to_config>'.format(sys.argv[0]))
        sys.exit(1)

    config_path = sys.argv[1]
    if not os.path.isfile(config_path):
        print('error: not a file "{}"'.format(config_path))
        sys.exit(1)

    egd = ExtractGnssData()

    egd.initialize(config_path)
    #egd.extract_gnss_data('2021%', 5000)
    egd.extract_gnss_data(5000)
    egd.cleanup()


if __name__ == '__main__':
    main()
