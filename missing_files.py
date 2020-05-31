#!/usr/bin/env python3
import os
import sys
import hashlib

from common.logger import setup_logger
logger = setup_logger(__file__)

"""
Checks if all files in directory tree exists in another
"""

class File(object):
    def __init__(self, path):
        assert os.path.isfile(path)
        self.path = path
        stat = os.stat(path)
        self.size = stat.st_size
        self._hash = None
        self._quickhash = None

    @property
    def hash(self):
        block_size = 65536
        if self._hash is None:
            self._hash = hashlib.md5()
            with open(self.path, 'rb') as f:
                fb = f.read(block_size)
                while len(fb) > 0:
                    self._hash.update(fb)
                    fb = f.read(block_size)

        return self._hash.hexdigest()
    
    @property
    def quickhash(self):
        self._quickhash = hashlib.md5()
        with open(self.path, 'rb') as f:
            self._quickhash.update(f.read(1024))
        
        return self._quickhash.hexdigest()

    def equal(self, other):
        if self.size != other.size:
            return False

        if self.quickhash != other.quickhash:
            return False

        if self.hash != other.hash:
            return False
        
        return True



class Directory(object):
    def __init__(self, path="."):
        assert os.path.isdir(path)

        self.content = []
        self.files_by_size = {}

        for root, folders, files in os.walk(path):
            for filename in files:
                fo = File(os.path.join(root, filename))
                self.content.append(fo)
                if fo.size not in self.files_by_size:
                    self.files_by_size[fo.size] = []
                self.files_by_size[fo.size].append(fo)

    def has_file(self, fileobject: File) -> bool:
        if fileobject.size not in self.files_by_size:
            return False
        
        for fo in self.files_by_size[fileobject.size]:
            if fo.quickhash == fileobject.quickhash and fo.hash == fileobject.hash:
                return True

        return False

    def has_all(self, other):
        missing_files = []
        for other_file in other.content:
            if not self.has_file(other_file):
                missing_files.append(other_file)

        logger.info("Found {} missing files".format(len(missing_files)))
        for f in missing_files:
            print(f.path)


def main():
    source, dest = sys.argv[1:]

    logger.info("Scanning source directory")
    s = Directory(source)

    logger.info("Scanning destination directory")
    d = Directory(dest)
    

    logger.info("Checking files")
    d.has_all(s)


if __name__ == "__main__":
    main()