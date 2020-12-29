#!/usr/bin/env python3

import os
import hashlib
import json
import argparse


IGNORES = ['.git', '.vscode']

class Directory(object):
    def __init__(self, directory, recurse=True, parent=None):
        print("Opening: {}".format(directory))
        self.directory = os.path.abspath(directory)
        self.subdirectories = {}
        self.content = sorted(os.listdir(directory))
        self.parent = parent
        self.depth = 0

        if recurse:
            self.scan()
    
    def scan(self):
        self.depth = 0
        for entry in self.content:
            if entry in IGNORES:
                continue
            fullpath = os.path.join(self.directory, entry)
            if os.path.isdir(fullpath):
                subdir = Directory(fullpath,  parent=self)
                self.subdirectories[entry] = subdir
                self.depth = max(self.depth, subdir.depth)

    def __eq__(self, other):
        if self.content != other.content:
            return False
        
        if len(self.subdirectories) != len(other.subdirectories):
            return False
        
        for name, sub in self.subdirectories.items():
            if name not in other.subdirectories:
                return False
            
            if sub != other.subdirectories[name]:
                return False

        return True

    @property
    def size(self):
        return len(self.content)
    
    @property
    def hash(self):
        h = hashlib.md5()
        h.update(json.dumps(self.content).encode('utf8'))
        for name, sub in self.subdirectories.items():
            h.update(sub.hash.encode('utf8'))
        
        return h.hexdigest()
    
    def hashes(self):
        _hashes = []
        _hashes.append((self.hash, self))
        
        for name, sub in self.subdirectories.items():
            _hashes += sub.hashes()  # [(sub.hash, sub)]
        
        return _hashes
    
    def duplicates(self):
        hashes = self.hashes()
        hashes = list(sorted(hashes, key=lambda x: x[0]))
        hashes = list(sorted(hashes, key=lambda x: -len(x[0])))

        result = {}

        for h in hashes:
            if h[0] not in result:
                result[h[0]] = [h[1]]
                continue

            if h[0] in result:
                if h[1] == result[h[0]][0]:
                    result[h[0]].append(h[1])

        

        result = {key: value for (key, value) in result.items() if len(value) > 1}
        output = {}
        for key, value in result.items():
            v = value[0]
            add = True
            while v.parent is not None:
                v = v.parent
                if v.hash in result:
                    add = False
            if add:
                output[key] = value
            
        return output
    
    def has_child(self, other):
        for subdir in self.subdirectories:
            if other.directory == os.path.join(self.directory, subdir):
                return True

        for h, sub in self.subdirectories.items():
            if sub.has_child(other):
                return True
        
        return False


def argparser():
    parser = argparse.ArgumentParser(description="Find duplicates in file system")
    parser.add_argument('--folders', action="store_true")
    parser.add_argument('--files', action="store_true")
    parser.add_argument('--dry-run', action="store_true", default=False)
    return parser

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


def folders():
    directory = Directory(".")
    print(" ")
    duplicates = directory.duplicates()
    for d, values in duplicates.items():
        print(d), 
        for v in values:
            print(f"* {v.directory}")
        print(" ")


def files(dry_run=False):
    found_files = {}
    for root, dirs, files in os.walk('.', topdown=True):
        dirs[:] = [d for d in dirs if d not in IGNORES]

        print("Scanning {}".format(root))
        for file in files:
            fullpath = os.path.join(root, file)
            depth = root.count(os.path.sep)
            stat = os.stat(fullpath)
            found_files[fullpath] = {
                'fullpath': fullpath,
                'depth': depth,
                'size': stat.st_size
            }
    
    print("Found {} files".format(len(found_files.keys())))

    files_by_size = {}
    for file, data in found_files.items():
        if data['size'] not in files_by_size:
            files_by_size[data['size']] = []
        
        files_by_size[data['size']].append(data)
    
    files_by_size = {key: value for (key, value) in files_by_size.items() if len(value) > 1}
    number_of_files = 0
    for key, value in files_by_size.items():
        number_of_files += len(value)
    print("{} files in {} sets".format(number_of_files, len(files_by_size.keys())))

    delete = []
    for size, files in files_by_size.items():
        for file in files:
            with open(file['fullpath'], 'rb') as f:
                h = hashlib.md5()
                h.update(f.read(max(1024 * 1024, size)))
                file['start'] = h.hexdigest()

        file_starts = set([file['start'] for file in files])
        if len(file_starts) == len(files):
            delete.append(size)
    
    for size in delete:
        del files_by_size[size]

    number_of_files = 0
    for key, value in files_by_size.items():
        number_of_files += len(value)
    print("{} files in {} sets".format(number_of_files, len(files_by_size.keys())))

    if not dry_run:
        print("Deleting files")
        for size, files in files_by_size.items():
            print("Size: {}".format(size))
            for file in files:
                print(file['fullpath'])
    

def main2():
    parser = argparser()
    args = parser.parse_args()

    if args.files:
        files(args.dry_run)
    else:
        folders()


if __name__ == "__main__":
    main2()