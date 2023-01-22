import sys
import os
import yaml
import psycopg2


def _load_config(config_path):
    if not os.path.isfile(config_path):
        print(f'error: not a file: {config_path}', file=sys.stderr)
        return None

    config_data = None
    with open(config_path, 'r') as config_stream:
        config_data = yaml.load(config_stream, Loader=yaml.FullLoader)

    return config_data


def _check_config_root_folder(config_data):
    if not 'root_folder' in config_data:
        return False
    folder = config_data['root_folder']
    if os.path.isdir(folder):
        print(f'info: use data from: {folder}', file=sys.stderr)
        return True
    else:
        print(f'error: not a dir: {folder}', file=sys.stderr)
        return False


def _check_config_db_connect(config_data):
    if not 'db_connect' in config_data:
        return False
    props = config_data['db_connect']
    for prop_name in ['user', 'password', 'host', 'database']:
        if not prop_name in props:
            print(
                f'error: incomplete DB connection, [{prop_name}] is not specified', file=sys.stderr)
            return False
    return True


def _make_db_connect(config_data):
    conn_obj = None
    try:
        conn_props = config_data['db_connect']
        conn_obj = psycopg2.connect(user=conn_props['user'], password=conn_props['password'],
                                    host=conn_props['host'], dbname=conn_props['database'])
    except psycopg2.Error as err:
        print(f'error: pg: {err.pgerror}', file=sys.stderr)
    return conn_obj


class BaseConfig:
    def __init__(self):
        self.config_data = None
        self.conn = None
        self.initialized = False

    def initialize(self, config_path):
        # load and check configuration file
        self.config_data = _load_config(config_path)
        if not self.config_data:
            print(f'error: unable to load {config_path}', file=sys.stderr)
            return False

        if not _check_config_root_folder(self.config_data):
            print(f'error: invalid config {config_path}', file=sys.stderr)
            return False

        if not _check_config_db_connect(self.config_data):
            print(f'error: invalid config {config_path}', file=sys.stderr)
            return False

        # open database connection
        self.conn = _make_db_connect(self.config_data)
        if not self.conn:
            print(f'error: unable to connect to database', file=sys.stderr)
            return False

        self.initialized = True
        return True

    def get_base_folder(self):
        return self.config_data['root_folder']

    def cleanup(self):
        self.config_data = None
        if self.conn:
            # close db connection
            self.conn.close()
            self.conn = None
        self.initialized = False
