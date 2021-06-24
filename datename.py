#!/usr/bin/env python3
import exiftool
from pathlib import Path
from hashlib import md5

HASHES = {}


def file_hash(f: Path):
    with f.open(mode='rb') as inp:
        h = md5()
        h.update(inp.read())
        return h.hexdigest()


def main():

    batch_size = 100
    idx = 0

    all_files = [str(f) for f in Path('.').glob('*.jpg')]

    while idx < len(all_files):
        files = all_files[idx:idx+batch_size]
        with exiftool.ExifTool() as et:
            metadata = et.get_metadata_batch(files)

        for d in metadata:
            old_name = d['SourceFile']
            if not 'EXIF:DateTimeOriginal' in d:
                print(f"Could not find datetime for {old_name}")
                continue

            new_base_name = d["EXIF:DateTimeOriginal"].replace(
                ':', '').replace(' ', '')
            new_name = new_base_name + '.jpg'
            if old_name == new_name:
                print(f"Skipping {old_name}")
                continue

            print(f"Rename {old_name} to {new_name}")
            old = Path(old_name)
            new = Path(new_name)

            if new.exists():
                print("New file already exists")
                old_stat = old.stat()
                new_stat = new.stat()

                if old_stat.st_size != new_stat.st_size:
                    new_name = f'{new_base_name}_{old_stat.st_size}.jpg'
                    new = Path(new_name)
                else:
                    old_hash = file_hash(old)
                    new_hash = file_hash(new)

                    if old_hash == new_hash:
                        print("Same file!")
                        old.replace(Path('duplicates/' + old_name))
                    continue

            old.rename(new)

        idx += batch_size


if __name__ == '__main__':
    main()
