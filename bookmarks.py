#!/usr/bin/env python3

import os
import sys
import json
from bs4 import BeautifulSoup, element
import argparse
from jinja2 import Template

from settings import SETTINGS

bookmark_template = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<!-- This is an automatically generated file.
     It will be read and overwritten.
     DO NOT EDIT! -->
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
{%- for item in children recursive %}
    {%- if item.type == 2 %}
{{ "    " * loop.depth }}<DT><H3 ADD_DATE="{{item.date}}" LAST_MODIFIED="{{item.date}}" PERSONAL_TOOLBAR_FOLDER="true">{{item.title}}</H3></DT>
{{ "    " * loop.depth }}<DL><p>{{ loop(item.children) }}
{{ "    " * loop.depth }}</p>
{{ "    " * loop.depth }}</DL>
    {%- endif %}
    {%- if item.type == 1 %}
{{ "    " * loop.depth }}<DT><A HREF="{{item.uri}}" ADD_DATE="{{item.date}}">{{item.title}}</A></DT>
    {%- endif %}
{%- endfor %}
</p></DL>
"""


BOOKMARK = 1
FOLDER = 2


def linkfolder(link):
    for parent in link.parents:
        if parent is None:
            raise Exception
        elif parent.name == 'dl':
            sibling = parent
            while sibling.previous_sibling is not None and (sibling.name != 'h3' or sibling.name != 'dt'):
                sibling = sibling.previous_sibling
            if sibling.name == 'h3':
                parent = linkfolder(sibling)
                # print("{} > {}".format(sibling.text, parent['title']))
                """
                if parent is not None:
                    if parent['title'] not in folders:
                        folders[parent['title']] = parent
                    else:
                        parent = folders[parent['title']]
                return {'title': sibling.text, 'parent': parent}
                """
                if parent is not None:
                    return parent + ">>>" + sibling.text
                else:
                    return sibling.text
        else:
            # print("Skipping {}".format(parent.name))
            continue

    return None


class Bookmarks(object):
    def __init__(self, filename: str = None):
        print("Filename: " + filename)
        self.folders = {
            "title": "bookmarks",
            "dateAdded": 0,
            "lastModified": 0,
            "type": FOLDER,
        }

        if '~' in filename:
            filename = os.path.expanduser(filename)

        if filename is not None:
            self.filename = filename

        if os.path.isfile(filename):
            self.load(filename)

    def load(self, filename: str):
        print("Loading bookmarks")
        if '~' in filename:
            filename = os.path.expanduser(filename)
        with open(filename, 'r') as f:
            self.folders = json.load(f)

    def save(self, filename: str = None):
        print("Saving bookmarks")
        if filename is None:
            filename = self.filename
        if '~' in filename:
            filename = os.path.expanduser(filename)
        if filename is None:
            filename = self.filename

        with open(filename, 'w') as f:
            json.dump(self.folders, f, indent=4)

    def get_folder(self, folder):
        sections = folder.split(">>>")
        cur_folder = self.folders
        for section in sections:
            found = False
            if 'children' not in cur_folder:
                cur_folder['children'] = []
            for f in cur_folder['children']:
                if f['title'] == section and f['type'] == FOLDER:
                    cur_folder = f
                    found = True
                    break
            if not found:
                cur_folder = self.add_folder(sections)
        return cur_folder

    def add_folder(self, sections):
        cur_folder = self.folders

        for section in sections:
            found = False

            if 'children' not in cur_folder:
                cur_folder['children'] = []

            for f in cur_folder['children']:
                if f['title'] == section and f['type'] == FOLDER:
                    cur_folder = f
                    found = True
                    break
            if not found:
                f = {
                    'title': section,
                    'type': FOLDER,
                    'dateAdded': 0,
                    'lastModified': 0,
                }
                cur_folder['children'].append(f)
                cur_folder = f
        return cur_folder

    def add_bookmark(self, bookmark):
        f = linkfolder(bookmark)
        folder = self.get_folder(f)
        if 'children' not in folder:
            folder['children'] = []

        for b in folder['children']:
            if b['type'] == BOOKMARK and b['uri'] == bookmark['href'] and b['title'] == bookmark.string:
                return

        folder['children'].append({
            'uri': bookmark['href'],
            'dateAdded': bookmark['add_date'],
            'lastModified': bookmark['add_date'],
            'title':  bookmark.string,
            "type": BOOKMARK,
        })

    def dump(self, outfile: str = 'bookmarks.html'):
        b = Template(bookmark_template)
        with open(outfile, 'w') as f:
            f.write(b.render(self.folders))


def argparser():
    parser = argparse.ArgumentParser("Handle bookmarks")
    parser.add_argument('--add', type=str, nargs=1)
    parser.add_argument('--dump', type=str, nargs=1)
    return parser


def add(filename: str):
    bookmarks = Bookmarks(SETTINGS.get('bookmarks', 'bookmarks.json'))

    with open(filename, 'r') as f:
        data = f.read()

    soup = BeautifulSoup(data, features="html.parser")

    # Find all links
    links = soup.find_all('a', recursive=True)

    # Find category for each link by checking parents
    for link in links:
        bookmarks.add_bookmark(link)

    bookmarks.save()


def dump(filename: str):
    bookmarks = Bookmarks(SETTINGS.get('bookmarks', 'bookmarks.json'))
    bookmarks.dump(filename)


def main():
    args = argparser().parse_args()
    if args.add:
        add(args.add[0])

    if args.dump:
        dump(args.dump[0])


if __name__ == "__main__":
    main()
