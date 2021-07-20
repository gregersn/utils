#!/usr/bin/env python3
import click
from typing import List, Union
import datetime
import time
from pathlib import Path
from makemkv import MakeMKV


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
    current_task: str
    state: int
    max: int

    def __init__(self):
        self.current_task = "Unknown"

    def progress(self, task_description: str, progress: int, _max: int):
        if task_description != self.current_task:
            print("")

            self.current_task = task_description

        print(f"\r{self.current_task}: {progress} / {_max}", end="")


class DVD:
    name: Union[str, None]
    information: str
    titles: List[DVDTitle]
    main_title: Union[DVDTitle, None]
    source: Path

    def __init__(self, filename: str, name: str = None):
        self.source = Path(filename)
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

    def open(self):
        self.__makemkv = MakeMKV(self.source, minlength=1)
        discinfo = self.__makemkv.info()
        self.convert_info(discinfo)
        self.__dirty = False

    def to_mkv(self, output):
        if self.__dirty:
            self.open()
        print(self)

        output_folder = Path(output).absolute()

        if self.name is not None:
            output_folder = output_folder / self.name
        else:
            raise NameError

        output_folder.mkdir(parents=True, exist_ok=True)

        progressor = MKVProgress()

        makemkv = MakeMKV(
            self.source, progress_handler=progressor.progress)

        for title in self.titles:
            outfile = output_folder / f"title_{title.index}-other.mkv"
            if title == self.main_title:
                print("Ripping main title")
                outfile = output_folder / (self.name + '.mkv')
            else:
                print(f"Ripping title {title.index}")

            makemkv.mkv(title.index, output_folder)

            infile = output_folder / title.file_output
            infile.rename(outfile)
            print("")

    def __repr__(self):
        return f"{self.name}, {self.information}, {len(self.titles)} titles"


@click.command()
@click.option('--name', help="Name/title of DVD", required=True)
@click.option('--source', help="Source", required=True)
@click.option('--output', help="Output folder", required=False)
def main(name, source, output=None):
    source = Path(source)
    assert source.exists()
    dvd = DVD(str(source),
              name=name)
    dvd.to_mkv(output or ".")


if __name__ == '__main__':
    main()
