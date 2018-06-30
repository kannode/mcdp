import os
import ssl
import sys
from collections import defaultdict

import yaml
from bs4 import Tag

from mcdp_utils_misc import write_data_to_file
from mcdp_utils_xml import get_minimal_html_document, stag


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

    ignore = ['docs-resources']
    for repo in repos:
        if 'docs' not in repo.name:
            continue
        if repo.name in ignore:
            continue

        forks = list(repo.get_forks())
        # print repo.name
        # print 'forks: %s' % forks
        res[str(repo.name)][str(repo.owner.login)] = repo

        for repo1 in forks:
            res[str(repo1.name)][str(repo1.owner.login)] = repo1

    res = dict(**res)


    html = get_minimal_html_document(title='List of duckumentation forks', stylesheet='style.css')
    body = html.body
    css = """
    
thead { font-weight: bold; }
td { padding: 5px; }
    
    """
    style =Tag(name='style')
    style.attrs['type'] = 'text/css'
    style.append(css)
    html.head.insert(0, style)

    from mcdp_docs.sync_from_circle import go_

    for repo in res:

        h = Tag(name='h3')
        h.append(repo)
        body.append(h)
        table = Tag(name='table')
        thead = Tag(name='thead')
        thead.append(stag('td', 'user'))
        thead.append(stag('td', 'github link'))
        thead.append(stag('td', 'builds'))
        table.append(thead)

        for username in res[repo]:
            print('\n%s - %s\n' % (repo, username))
            d = os.path.join(d0, repo, username)
            fn = os.path.join(d, 'index.html')

            builds = go_(username, repo, d, fn, repo=res[repo][username], limit=5)

            print('\n%s - %s\n' % (repo, username))


            tr = Tag(name='tr')
            tr.append(stag('td', username))

            td = Tag(name='td')
            td.append(stag('a', 'fork', href='http://github.com/%s/%s/' % (username, repo)))
            tr.append(td)

            td = Tag(name='td')
            if len(builds) > 0:
                td.append(stag('a', 'builds', href='%s/%s/index.html' % (repo, username)))
            else:
                s = 'Circle builds not activated'
                td.append(s)
            tr.append(td)

            table.append(tr)

        body.append(table)

    fn = os.path.join(d0, 'index.html')
    write_data_to_file( str(html), fn)

if __name__ == '__main__':
    go()
