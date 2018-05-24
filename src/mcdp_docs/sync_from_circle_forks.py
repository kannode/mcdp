import os
import ssl
import sys


def go():
    username = sys.argv[1]
    project = sys.argv[2]
    d0 = sys.argv[3]
    fn = sys.argv[4]

    print('username: %s' % username)
    print('project: %s' % project)
    print('d0: %s' % d0)
    print('fn: %s' % fn)

    from github import Github
    if not 'GITHUB_TOKEN' in os.environ:
        raise Exception()
    else:
        github_token = os.environ['GITHUB_TOKEN']
        try:
            g = Github(github_token)
            active_branches = [_.name for _ in g.get_organization(username).get_repo(project).get_branches()]
        except ssl.SSLError as e:
            print('error: %s' % e)
            raise Exception(str(e))

    org = g.get_organization(username)
    repo = org.get_repo(project)
    forks = repo.get_forks()
    for fork in forks:
        print fork


if __name__ == '__main__':
    go()
