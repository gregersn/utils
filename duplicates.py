#!/usr/bin/env python3

import os
import hashlib
import json


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
                    print("v.hash in result")
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


def main2():
    directory = Directory(".")
    duplicates = directory.duplicates()
    for d, values in duplicates.items():
        print(d, [v.directory for v in values])
        print(" ")


if __name__ == "__main__":
    main2()