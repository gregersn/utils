#!/usr/bin/env python3
import click
from typing import List, Union
import datetime
import time
from pathlib import Path
from makemkv import MakeMKV

import logging

logging.getLogger("makemkv").setLevel(logging.ERROR)


class DVDTitle:
    duration: float
    index: int
    file_output: str

    def __init__(self, index: int):
        self.index = index

    def convert_info(self, info):
        x = time.strptime(info['length'], '%H:%M:%S')
        duration = datetime.timedelta(
            hours=x.tm_hour, minutes=x.tm_min, seconds=x.tm_sec).total_seconds()

        self.duration = duration
        self.file_output = info['file_output']

    def __repr__(self):
        return f"Title {self.index}, duration: {self.duration}"


class MKVProgress:
    current_task: Union[str, None]
    state: int
    max: int

    def __init__(self):
        self.current_task = None

    def reset(self):
        self.current_task = None

    def progress(self, task_description: str, progress: int, _max: int):
        if self.current_task is not None and task_description != self.current_task:
            print(f"\r*** {self.current_task}: {int((1.0) * 100)}%")

        self.current_task = task_description

        print(
            f"\r*** {self.current_task}: {int((progress / _max) * 100)}%", end="")


class DVD:
    name: Union[str, None]
    information: str
    titles: List[DVDTitle]
    main_title: Union[DVDTitle, None]
    sources: List[Path]

    def __init__(self, filename: List[str], name: str = None):
        self.sources = [Path(f) for f in filename]
        self.titles = []
        self.__dirty = True
        self.main_title = None
        self.name = name

    def convert_info(self, info):
        disc_info = info.get('disc', {})

        if self.name is None:
            self.name = disc_info.get('name', 'Unnamed')
        self.information = disc_info.get('information', '')

        self.titles = []
        for idx, title in enumerate(info.get('titles', [])):
            t = DVDTitle(idx)
            t.convert_info(title)
            self.titles.append(t)
            if not self.main_title:
                self.main_title = t
            else:
                if t.duration > self.main_title.duration:
                    self.main_title = t

    def open(self, source: Path):
        self.__makemkv = MakeMKV(source, minlength=1)
        discinfo = self.__makemkv.info()
        self.convert_info(discinfo)
        self.__dirty = False

    def to_mkv(self, output):
        output_folder = Path(output).absolute()

        if self.name is not None:
            output_folder = output_folder / self.name
        else:
            raise NameError

        output_folder.mkdir(parents=True, exist_ok=True)

        progressor = MKVProgress()

        for i, source in enumerate(self.sources):
            self.open(source)
            makemkv = MakeMKV(
                source, progress_handler=progressor.progress)

            for title in self.titles:
                progressor.reset()
                outfile = output_folder / \
                    f"title_{i + 1}_{title.index}-other.mkv"
                if title == self.main_title and i == 0:
                    print("\n** Ripping main title")
                    outfile = output_folder / (self.name + '.mkv')
                else:
                    print(
                        f"\n** Ripping title {title.index + 1} / {len(self.titles)}")

                makemkv.mkv(title.index, output_folder)

                infile = output_folder / title.file_output
                infile.rename(outfile)
                print("")

    def __repr__(self):
        return f"* {self.name}, {self.information}, {len(self.titles)} title(s)."


@click.command()
@click.option('--source', help="Source", required=True)
@click.option('--name', help="Name/title of DVD", required=False)
@click.option('--output', help="Output folder", required=False)
def main(source, name=None, output=None):
    source = Path(source)
    assert source.exists()

    if source.is_dir():
        discs = []
        files = source.glob('*')
        for file in files:
            if file.suffix in ['.iso', '.ISO']:
                discs.append(file)
        # print([file for file in discs])
        name = source.parts[-1]

        dvd = DVD(discs,
                  name=name)
        dvd.to_mkv(output or ".")

    else:
        dvd = DVD(str(source),
                  name=name)
        dvd.to_mkv(output or ".")


if __name__ == '__main__':
    main()
