#!/usr/bin/env python3

import os
from typing import List, Optional, TypedDict
import click
import shutil
import datetime
from pathlib import Path
import pyexiv2

from logging import getLogger, basicConfig

basicConfig()
logger = getLogger("picture_copy")
logger.setLevel(os.environ.get('LOGLEVEL', 'WARNING'))

EXTENSIONS = ('nef', 'mov', 'jpg', 'mp4')


class PictureFile(TypedDict):
    folder: Path
    filename: str
    timestamp: datetime.datetime


class FileToCopy(TypedDict):
    file: PictureFile
    copy: bool
    dest_folder: Optional[Path]


def find_files(folder: Path):
    logger.info(f"Finding files in {folder}")
    found_files: List[PictureFile] = []
    for root, _, files in os.walk(folder):
        logger.info(f"Going into {root}")
        for file in files:
            file_info = Path(root) / file
            stat = file_info.stat()
            file_modification_time = datetime.datetime.fromtimestamp(
                stat.st_mtime)
            found_files.append({
                'folder': Path(root),
                'filename': file,
                'timestamp': file_modification_time
            })

    return found_files


def prune_files(files: List[PictureFile], dest_folder: Path):
    outfiles: List[FileToCopy] = []
    for file in files:
        outfile: FileToCopy = {'file': file, 'copy': True, 'dest_folder': None}

        ts = file['timestamp']
        picture_dest_folder = (dest_folder / str(ts.year) /
                               str(ts.month).zfill(2))
        outfile['dest_folder'] = picture_dest_folder

        extension = file['filename'].split('.')[-1].lower()

        if extension not in EXTENSIONS:
            outfile['copy'] = False

        if (picture_dest_folder / file['filename']).exists():
            outfile['copy'] = False

        outfiles.append(outfile)

    return outfiles


def copy_files(files: List[FileToCopy], dry_run: bool = True):
    for copyfile in files:
        source = copyfile['file']
        if copyfile['copy']:
            print(f"Copying {source['filename']} to {copyfile['dest_folder']}")
            if copyfile['dest_folder'] and copyfile['dest_folder'].exists():
                logger.info("Destination folder exists: %s")
                if not copyfile['dest_folder'].is_dir():
                    logger.error("%s is not a folder", copyfile['dest_folder'])
                    raise IOError
            else:
                logger.info("Destination folder does not exist")
                if not dry_run and copyfile['dest_folder']:
                    logger.debug(f"Creating folder {copyfile['dest_folder']}")
                    copyfile['dest_folder'].mkdir(parents=True)

            if not dry_run and copyfile['dest_folder']:
                shutil.copy2((source['folder'] / source['filename']),
                             copyfile['dest_folder'])

        else:
            logger.debug(f"Skipping {source['filename']}, destination exists.")


@click.command()
@click.argument("src", type=click.Path(exists=True, path_type=Path))
@click.argument("dst", type=click.Path(exists=True, path_type=Path))
@click.option('--dry-run/--no-dry-run', default=False)
def main(src: Path, dst: Path, dry_run: bool = False):
    """
    Picture Copy

    SRC Folder to find pictures in

    DST Folder to copy pictures into
    """
    source = src.expanduser()
    dest = dst.expanduser()

    source_files = find_files(source)
    files_to_copy = prune_files(source_files, dest)

    copy_files(files_to_copy, dry_run=dry_run)


if __name__ == "__main__":
    main()
