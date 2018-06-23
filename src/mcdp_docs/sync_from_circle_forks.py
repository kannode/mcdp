import os
import ssl
import sys
from collections import defaultdict

import yaml


def go():
    ''' Find all the forks of the repos containing 'docs' '''
    username = sys.argv[1]
    d0 = sys.argv[2]
    from github import Github
    if not 'GITHUB_TOKEN' in os.environ:
        raise Exception()
    else:
        github_token = os.environ['GITHUB_TOKEN']
        try:
            g = Github(github_token)
            # active_branches = [_.name for _ in g.get_organization(username).get_repo(project).get_branches()]
        except ssl.SSLError as e:
            print('error: %s' % e)
            raise Exception(str(e))

    org = g.get_organization(username)
    repos = list(org.get_repos())
    res = defaultdict(dict)

    for repo in repos:
        if 'docs' not in repo.name:
            continue

        forks = list(repo.get_forks())
        # print repo.name
        # print 'forks: %s' % forks
        res[str(repo.name)][str(repo.owner.login)] = repo

        for repo1 in forks:
            res[str(repo1.name)][str(repo1.owner.login)] = repo1

    res = dict(**res)
    print yaml.dump(res, allow_unicode=True)

    from mcdp_docs.sync_from_circle import go_

    for repo in res:
        for username in res[repo]:
            print('\n%s - %s\n' % (repo, username))
            d = os.path.join(d0, repo, username)
            fn = os.path.join(d, 'index.html')

            go_(username, repo, d, fn, repo=res[repo][username])


if __name__ == '__main__':
    go()
