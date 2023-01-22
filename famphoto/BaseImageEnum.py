import sys
import os
from famphoto.BaseConfig import BaseConfig


def _check_excluded_name(name, exclude_names):
    if not name:
        print('warning: empty name!', file=sys.stderr)
        return True
    name_lowered = name.lower()
    for exclude_entry in exclude_names:
        if name_lowered.startswith(exclude_entry):
            return True
    return False


class BaseImageEnum(BaseConfig):
    def __init__(self):
        super().__init__()

    def handle_image_file(self, image_path, image_name, subfolder):
        pass

    def enumerate_image_files(self, exclude_folder_names):
        if not self.initialized:
            print(f'error: not initialized', file=sys.stderr)
            return

        # basic folder for images
        root_folder = self.get_base_folder()
        root_folder_len = len(root_folder)

        # counters
        folder_count = 0
        image_count = 0

        # walk over all files
        for immediate_folder, _, files in os.walk(root_folder, topdown=False, followlinks=False):
            # exclude some folders
            current_folder = os.path.basename(immediate_folder)
            if _check_excluded_name(current_folder, exclude_folder_names):
                print(
                    f'warning: exclude folder {immediate_folder}', file=sys.stderr)
                continue

            folder_count += 1

            immediate_folder_len = len(immediate_folder)
            for file_name in files:
                # only JPEG files
                _, file_ext = os.path.splitext(file_name)
                if file_ext.lower() in ['.jpg', '.jpeg']:
                    file_path = os.path.join(immediate_folder, file_name)
                    if immediate_folder_len > root_folder_len:
                        subfolder = immediate_folder[len(root_folder) + 1:]
                    else:
                        subfolder = '.'

                    self.handle_image_file(file_path, file_name, subfolder)

                    image_count += 1

        # summary
        print(
            f'info: enumerated folders={folder_count}, images={image_count}', file=sys.stderr)
