#!/usr/bin/env python3

import os
import sys
from typing import Any, Union
import click
from pathlib import Path
from paramiko import SSHClient
from scp import SCPClient
from scp import SCPException


def progress(filename: Path, size: Union[int, float], sent: Union[int, float]):
    sys.stdout.write("%s's progress: %.2f%%   \r" %
                     (filename, float(sent)/float(size)*100))


@click.command()
@click.argument("source", type=click.Path(path_type=Path, exists=True))
@click.argument("paths", type=click.Path(path_type=Path, exists=False), nargs=-1)
def main(source: Path, paths: Any):
    """
    Upload SOURCE to predefined host, return url.

    SOURCE: string, source file

    DESTINATION: string, destination folder
    """

    filehost = os.environ.get("FILEHOST")
    filedir = os.environ.get("FILEDIR", "public_html")
    fileuser = os.environ.get("FILEUSER", os.environ.get("USER"))

    if len(paths) > 0:
        source_files = [source, ] + list(paths[:-1])
        dest_folder = paths[-1]
    else:
        source_files = [source, ]
        dest_folder = ""

    if not filehost:
        print("Error: FILEHOST is not defined in the environment.")
        sys.exit(1)

    ssh = SSHClient()
    ssh.load_system_host_keys()
    ssh.connect(filehost)

    base_url = f"https://{filehost}/~{fileuser}"

    if dest_folder:
        base_url += f"/{dest_folder}"

    scp = SCPClient(ssh.get_transport(), progress=progress)
    for source_file in source_files:
        try:
            scp.put(source_file, remote_path=f"{filedir}/{dest_folder}")
            url = f"{base_url}/{source_file.name}"
            print(f"Uploaded file to: {url}")
        except SCPException as e:
            print(f"Could not upload file {source} to {filedir}/{dest_folder}")
            print(e)


if __name__ == '__main__':
    main()
