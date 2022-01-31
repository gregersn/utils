#!/usr/bin/env python3
import os
import re
import sys
import shutil
from pathlib import Path
import hashlib
from typing import Dict, Any, List, Optional, TypedDict, Union, Tuple

import json
import click


INDEX_FILE_NAME = ".GSN_file_index.json"


class FileInfo(TypedDict):
    path: str
    size: int
    hash: str


class JsonEncoder(json.JSONEncoder):
    def default(self, o: Any):
        if isinstance(o, File):
            return o.to_dict()
        return json.JSONEncoder.default(self, o)


class File:
    path: Path
    size: int
    _quickhash: Any

    def __init__(self, path: Path, size: Optional[int] = None, quickhash: Optional[str] = None):
        self.path = path
        self.size = size or path.stat().st_size
        self._hash = None
        self._quickhash = quickhash
        self.hash_depth = 0

        self.quickhash

    @classmethod
    def from_dict(cls, data: FileInfo, parent: Path):
        return cls(parent / Path(data['path']), data['size'], data['hash'])

    def to_dict(self):
        return {'path': str(self.path), 'size': self.size, 'hash': self.quickhash}

    @property
    def quickhash(self) -> str:
        if self._quickhash is None:
            self._quickhash = hashlib.md5()
            with open(self.path, 'rb') as f:
                self._quickhash.update(f.read(1024))

        if isinstance(self._quickhash, str):
            return self._quickhash
        return self._quickhash.hexdigest()

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

    def __repr__(self):
        return f'<File {self.path}>'


class FileIndex:
    path: Path
    _index: Dict[str, File]
    _index_path: Path

    def __init__(self, path: Path = Path(".")):
        self.path = path
        self._index = {}

    def load(self, go_upwards: bool = True):
        filename = self.path / INDEX_FILE_NAME

        if not filename.is_file() and go_upwards and str(self.path.absolute()) != self.path.root:
            parent = self.path.absolute()
            while str(parent) != parent.root and not (parent / INDEX_FILE_NAME).is_file():
                parent = parent.parent
                filename = parent / INDEX_FILE_NAME

        if not filename.is_file():
            raise IndexError("No fileindex found.")

        with open(filename, encoding="utf8") as f:
            t_index = json.load(f)
            self._index_path = filename

            self._index = {}
            for k, v in t_index.items():
                self._index[k] = File.from_dict(
                    v, parent=self._index_path.parent)

    def update(self):
        cwd = Path.cwd()
        os.chdir(self.path)
        for root, _, files in os.walk('.'):
            r = Path(root)
            for filename in files:
                path = r / filename
                if not path.is_file():
                    continue

                file_object = File(path)

                self.add_file(file_object)
        os.chdir(cwd)
        print(Path.cwd())

    def add_file(self, file_object: File):
        print("Adding", file_object)
        self._index[str(file_object.path)] = file_object

    def save(self):
        with open(self.path / INDEX_FILE_NAME, 'w') as f:
            json.dump(self._index, f, cls=JsonEncoder, indent=4)

    @property
    def index(self):
        def path_filter(x: Tuple[Any, File]):
            _, v = x
            full_path = self._index_path.parent / v.path
            if full_path.absolute().is_relative_to(self.path.absolute()):
                return True
            return False
        return dict(filter(path_filter, self._index.items()))

    def by_size(self):
        by_size: Dict[int, List[File]] = {}
        for _, v in self.index.items():
            if v.size not in by_size:
                by_size[v.size] = []

            by_size[v.size].append(v)

        return by_size

    def by_hash(self):
        by_hash: Dict[str, List[File]] = {}

        for _, v in self.index.items():
            if v.quickhash not in by_hash:
                by_hash[v.quickhash] = []

            by_hash[v.quickhash].append(v)

        return by_hash

    def missing_from(self, other: 'FileIndex') -> List[File]:
        print("Loading destination index")
        self.load()
        print("Loading source index")
        other.load()
        other_sizes = other.by_size()

        missing: List[File] = []
    
        print("Comparing files")
        for _, my_file in self.index.items():
            found = False
            if not my_file.size in other_sizes:
                missing.append(my_file)
                print("Missing file: ", my_file)
                continue

            same_size = other_sizes[my_file.size]
            for s in same_size:
                if s.quickhash != my_file.quickhash:
                    continue

                if s.hash == my_file.hash:
                    found = True
                    break

            if not found:
                print("Missing file: ", my_file)
                missing.append(my_file)

        return missing


@click.group()
def cli():
    pass


@cli.command()
@click.argument('folder', type=click.Path(path_type=Path, file_okay=False, exists=True))
def create(folder: Path):
    """Create a file index for FOLDER."""
    index = FileIndex(folder)
    index.update()
    index.save()


@cli.command()
@click.argument('folder', type=click.Path(path_type=Path, file_okay=False, exists=True))
@click.option("--by-size", is_flag=True)
@click.option("--by-hash", is_flag=True)
def list(folder: Path, by_size: bool = False, by_hash: bool = False):
    """Print a list of indexed files in FOLDER."""
    index = FileIndex(folder)
    try:
        index.load()
    except IndexError as e:
        print(e)
        sys.exit(1)

    items = {}
    if by_size:
        print("List items by size")
        items = index.by_size()
    elif by_hash:
        items = index.by_hash()
    else:
        items = index.index

    for k, v in items.items():
        print(k, v)


@cli.command()
@click.argument("destination", type=click.Path(path_type=Path, file_okay=False, exists=True))
@click.argument("source", type=click.Path(path_type=Path, file_okay=False, exists=True))
@click.option("--min-size", type=int, help="Minimum file size to consider.")
def compare(destination: Path, source: Path, min_size: int = 1):
    """Check if all files in SOURCE exists in DESTINATION."""

    print(
        f"Check if all files in {source} of {min_size} bytes or more exists in {destination}.")

    source_index = FileIndex(source)
    destination_index = FileIndex(destination)

    missing = source_index.missing_from(destination_index)

    for f in missing:
        print(f)

@cli.command()
@click.argument("folder", type=click.Path(path_type=Path, file_okay=False, exists=True))
@click.argument("missing_files", type=click.Path(path_type=Path, dir_okay=False, exists=True))
@click.option("--delete", is_flag=True, help="Really delete files.")
def delete(folder: Path, missing_files: Path, delete: bool = False):
    """Delete all the files that are not missing when compared to some other folder."""

    if delete:
        print("THIS IS NOT A DRILL, FILES WILL BE DELETED!")

    print("Loading data from previous run")
    missing_files_path: List[str] = []

    filename_re = re.compile('<File (.*)>')

    with open(missing_files) as f:
        while line := f.readline():
            file_path = filename_re.match(line)
            if file_path:
                missing_files_path.append(file_path.group(1))

    print("Loading fileindex")
    folder_index = FileIndex(folder)
    print("Reading file info")
    folder_index.load()
    
    print("Running through files.")
    for path, file_info in folder_index.index.items():
        if not str(file_info.path) in missing_files_path:
            if delete:
                print(f"Will delete: {path}")
                # Path(path).unlink()
                destination = Path(f"u/deleted/{path}").parent
                os.makedirs(destination, exist_ok=True)
                try:
                    shutil.move(file_info.path, f"u/deleted/{path}")
                except FileNotFoundError:
                    print("Skipping file not found.")
            else:
                print(f"File to delete: {path}")
        else:
            print(f"File missing from destination: {path}")
    



if __name__ == "__main__":
    cli()
