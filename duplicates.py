#!/usr/bin/env python3

import os
import json

def main():
    folders = {}

    for root, dirs, files in os.walk('.'):
        print("Checking folder: {}".format(root))
        if root not in folders:
            folders[root] = {
                'files': files,
                'dirs': dirs
            }
    print("...done checking folders\n")

    folders_by_content = {}

    print("Sorting by content")
    for folder, items in folders.items():
        items_json = json.dumps(items)
        if items_json not in folders_by_content:
            folders_by_content[items_json] = []
        
        folders_by_content[items_json].append(folder)
    print("...done\n")
    for content, folders in folders_by_content.items():
        if len(folders) > 1:
            print("Folders that might be equal:")
            print(", ".join(folders))
            print("")


if __name__ == "__main__":
    main()