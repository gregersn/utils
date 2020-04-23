#!/usr/bin/env python3

import os

from git import Repo


def find_repositories():
    repositories = []
    for root, folders, files in os.walk('.'):
        if '.git' in folders:
            repositories.append(root)
    
    return repositories

def check_repos(folders):
    repos = []
    for folder in folders:
        repos.append(check_repo(folder))

    return repos

def check_repo(folder):
    print("Checking repos in {}".format(folder))
    repo = Repo(folder)

    first_commit = None

    if not repo.bare:
        config = repo.config_reader()

        heads = repo.heads
        if hasattr(heads, 'master'):
            for first_commit in repo.iter_commits():
                pass    

    return {
        'first_commit': first_commit.hexsha if first_commit is not None else None,
        'folder': folder,
        'dirty': repo.is_dirty()
    }

def print_report(repos):
    repos = sorted(repos, key=lambda x: x['first_commit'] if x['first_commit'] is not None else "")
    prev = None
    for repo in repos:
        if prev is not None and prev['first_commit'] == repo['first_commit']:
            equal = "^"
        else:
            equal = " "

        print("{}{}: {}".format(equal, repo['first_commit'], repo['folder']))
        prev = repo

def main():
    repos = find_repositories()
    found = check_repos(repos)
    print_report(found)

if __name__ == "__main__":
    main()