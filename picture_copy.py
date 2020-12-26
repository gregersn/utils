#!/usr/bin/env python3

import os
import sys
import shutil
import datetime
import pathlib
import pyexiv2

EXTENSIONS = ('nef', 'mov')

def find_files(folder: str):
    print(folder)
    found_files = []
    for root, folders, files in os.walk(folder):
        for file in files:
            file_info = pathlib.Path(os.path.join(root, file))
            stat = file_info.stat()
            file_modification_time = datetime.datetime.fromtimestamp(stat.st_mtime)
            found_files.append({
                'folder': root,
                'filename': file,
                'timestamp': file_modification_time
            })
    
    return found_files

def prune_files(files, dest_folder):
    for file in files:
        file['copy'] = True

        ts = file['timestamp']
        picture_dest_folder = os.path.join(dest_folder, str(ts.year), str(ts.month).zfill(2))
        file['dest_folder'] = picture_dest_folder

        extension = file['filename'].split('.')[-1].lower()

        if extension not in EXTENSIONS:
            file['copy'] = False

        if os.path.exists(os.path.join(picture_dest_folder, file['filename'])):
            file['copy'] = False

    return files

def copy_files(files):
    for file in files:
        if file['copy']:
            print(f"Copying {file['filename']}")
            if os.path.exists(file['dest_folder']):
                print("Destination folder exists")
                if not os.path.isdir(file['dest_folder']):
                    print("... but is not a folder")
                    raise IOError
            else:
                print("Destination folder does not exist")
                os.makedirs(file['dest_folder'])
    
            shutil.copy2(os.path.join(file['folder'], file['filename']), file['dest_folder'])         

        else:
            print(f"Not copying {file['filename']}")

def main():  
    source = sys.argv[1]
    dest = "."

    if len(sys.argv) > 2:
        dest = sys.argv[2]

    if '~' in source:
        source = os.path.expanduser(source)
    
    if '~' in dest:
        dest = os.path.expanduser(dest)


    source_files = find_files(source)
    files_to_copy = prune_files(source_files, dest)

    copy_files(files_to_copy)


if __name__ == "__main__":
    main()
