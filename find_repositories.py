#!/usr/bin/env python3

import os

import git
from git import Repo

from common.logger import setup_logger
logger = setup_logger(__file__)

def find_repositories():
    logger.info("Finding repositories")
    repositories = []
    for root, folders, files in os.walk('.'):
        logger.debug("In folder: {}".format(root))
        if '.git' in folders:
            logger.info("Found repository in: {}".format(root))
            repositories.append(root)
    
    return repositories

def check_repos(folders):
    logger.info("Checking {} repos".format(len(folders)))
    repos = []
    for folder in folders:
        check = check_repo(folder)
        if check is not None:
            repos.append(check)

    return repos

def check_repo(folder):
    logger.info("Checking repo in {}".format(folder))
    repo = None
    try:
        repo = Repo(folder)
    except git.exc.InvalidGitRepositoryError as e:
        logger.error("Invalid repository {}".format(e))
        return None

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
    logger.debug("Printing report")
    print_report(found)

if __name__ == "__main__":
    main()