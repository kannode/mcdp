# -*- coding: utf-8 -*-
import datetime
import fnmatch
import logging
import math
import os
import ssl
import sys
import tarfile
from collections import OrderedDict, defaultdict, namedtuple

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

import dateutil.parser
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from circleclient import circleclient
import dateutil.parser
import pytz
import yaml


class Build(object):

    def __init__(self, r, artefacts):
        self.r = r
        self.c0 = self.r['all_commit_details'][0]
        self.artefacts = artefacts

    def __repr__(self):
        return 'Build(%s)' % (self.get_build_num())

    def get_build_num(self):
        return self.r['build_num']

    def get_outcome(self):
        outcome = self.r['outcome']
        if outcome is None:
            if self.get_start_time() is None:
                outcome = 'queued'
            else:
                outcome = 'processing'
        if outcome == 'success':
            if not self.artefacts:
                outcome = 'completed_no_output'
        return outcome

    def get_outcome_string(self):
        strings = {
            'success': 'Success',
            'queued': 'Queued',
            'canceled': 'Canceled',
            'failed': 'Failed',
            'no_tests': 'No tests',
            'timedout': 'Timed out',
            'completed_no_output': 'No artefacts',
        }
        outcome = self.get_outcome()

        return strings.get(outcome, outcome)

    def get_start_time(self):
        start_time = self.r['start_time']
        if start_time is not None:
            start_time = dateutil.parser.parse(start_time)
        return start_time

    def get_stop_time(self):
        stop_time = self.r['stop_time']
        if stop_time is not None:
            stop_time = dateutil.parser.parse(stop_time)
        return stop_time

    def get_commit(self):

        return self.c0['commit']

    def get_branch(self):
        return self.r['branch']

    def has_artefacts(self):
        return len(self.artefacts) > 0

    def get_commit_url(self):
        return self.c0['commit_url']

    def get_build_url(self):
        return self.r['build_url']

    def get_avatar_url(self):
        login = self.c0['committer_login']
        avatar_url = 'https://avatars.githubusercontent.com/%s?size=64' % login
        return avatar_url

    def get_subject(self):
        return self.c0['subject']

    def get_author_name(self):
        return self.c0['committer_name']

    def get_duration_human(self):
        stop_time = self.get_stop_time()
        start_time = self.get_start_time()
        if stop_time is not None and start_time is not None:
            duration = stop_time - start_time
            duration_human = duration_compact(duration.total_seconds())
        else:
            # duration = None
            duration_human = None
        return duration_human


def read_build(client, username, project, token, r, d0):
    build_num = r['build_num']

    has_artifacts = r.get('has_artifacts', False)

    out_build_dir = os.path.join(d0, project, 'builds')
    d_build = os.path.join(out_build_dir, str(build_num))

    if os.path.exists(d_build):
        #            print('Already existing %s' % d)
        pass
    else:
        if r['outcome'] is not None:
            os.makedirs(d_build)
            if has_artifacts:
                print('collecting artifacts for %s' % build_num)
                artifacts = client.build.artifacts(username, project, build_num)

                path2url = collect(artifacts, token)

                PACK = 'out/package.tgz'
                if PACK in path2url:
                    f = os.path.join(d_build, 'dest.tgz')
                    download_to(f, path2url[PACK])

                    tf = tarfile.open(f, 'r:gz')
                    tf.extractall(d_build)
                    os.unlink(tf)

    #     try_look_for(os.path.join(d_build, 'out/split/index.html'), 'html')
    #     try_look_for(os.path.join(d_build, 'out.pdf'), 'PDF')

    # if artefacts:
    #     print(artefacts)
    artifacts = get_artefacts(d0, d_build)
    return Build(r=r, artefacts=artifacts)


Artefact = namedtuple('Artefact', 'display group rel found')


def get_artefacts(d0, d_build):
    """

    :param d0:
    :param d_build: where the artefacts are
    :return: list of Artefacts
    """
    artefacts = []

    def try_look_for(group_, f1, display_):
        if not os.path.exists(f1):
            logger.error('target %r does not exist' % f1)
            found = False
            rel = None
        else:
            found = True
            rel = os.path.relpath(f1, d0)
        artefacts.append(Artefact(display=display_, group=group_, rel=rel, found=found))

    pattern = '*.manifest.yaml'
    nfiles = 0
    for fn in locate_files(d_build, pattern):
        nfiles += 1
        # print('found manifest file %s' % fn)
        with open(fn) as f:
            entries = yaml.load(f.read())

        # print('fn = %s' % fn)
        # print('d_build = %s' % d_build)
        # print('fn2 = %s' % fn.replace(d_build+'/', ''))

        group = (fn.replace(d_build + '/', '')).split('/')[0]

        for e in entries:
            filename = e['filename']
            display = e['display']

            target = os.path.join(os.path.dirname(fn), filename)
            try_look_for(group, target, display)

    if nfiles == 0:
        # print('Could not find manifest files')
        pass

    return artefacts


class NoSuccess(Exception):
    pass


def get_first_succesfull(builds):
    for b in builds:
        if b.get_outcome() == 'success':
            return b
    raise NoSuccess()


def get_first_unsuccesfull(builds):
    for b in builds:
        if b.get_outcome() != 'success':
            return b
    raise NoSuccess()


def get_situation():
    pass


class BranchStatus(object):

    def __init__(self, last_failure, last_success, builds):
        self.last_failure = last_failure
        self.last_success = last_success
        self.builds = builds


def get_branch2status(builds):
    branch2status = OrderedDict()
    branch2builds = defaultdict(list)
    for build in builds.values():
        branch2builds[build.get_branch()].append(build)
    for branch, branch_builds in branch2builds.items():
        # get first build that is successful
        try:
            last_success = get_first_succesfull(branch_builds)
            print('branch %s: last success %s' % (branch, last_success))
        except NoSuccess:
            last_success = None
            print('branch %s: no builds' % branch)

        try:
            last_failure = get_first_unsuccesfull(branch_builds)
            print('branch %s: last failure %s' % (branch, last_failure))
        except NoSuccess:
            last_failure = None
            print('branch %s: no builds' % branch)

        if last_success and last_failure:
            if last_failure.get_build_num() < last_success.get_build_num():
                last_failure = None

        bs = BranchStatus(last_failure, last_success, branch_builds)
        branch2status[branch] = bs
    return branch2status


def go():
    now = datetime.datetime.now(tz=pytz.utc)
    token = os.environ['CIRCLE_TOKEN']

    client = circleclient.CircleClient(token)
    # print client.projects.list_projects()
    # print client.build.recent_all_projects()

    username = sys.argv[1]
    project = sys.argv[2]
    d0 = sys.argv[3]
    fn = sys.argv[4]

    print('username: %s' % username)
    print('project: %s' % project)
    print('d0: %s' % d0)
    print('fn: %s' % fn)
    print('circle token: %s' % token)

    from github import Github
    if not 'GITHUB_TOKEN' in os.environ:
        print('Set GITHUB_TOKEN for me to be smarter')
        active_branches = None
    else:
        github_token = os.environ['GITHUB_TOKEN']
        try:
            g = Github(github_token)
            active_branches = [_.name for _ in g.get_organization(username).get_repo(project).get_branches()]
        except ssl.SSLError as e:
            print('error: %s' % e)
            active_branches = None

    print('active branches: %s' % active_branches)
    res = client.build.recent(username, project, limit=50, offset=0)

    builds = OrderedDict()

    for r in res:
        #        print yaml.dump(r)
        if not r['all_commit_details']:
            print('skipping %s' % r['build_num'])
            continue
        build = read_build(client, username, project, token, r, d0)
        builds[build.get_build_num()] = build

    body = Tag(name='body')

    template = TEMPLATE
    template = template.replace('DATE', str(date_tag(now)))
    parsed = parse_html(template)
    table1 = get_build_table(builds)
    table2 = get_branch_table(d0, project, builds, active_branches)
    parsed.find(id='table1').replace_with(table1)
    parsed.find(id='table2').replace_with(table2)
    body.append(parsed)
    html = Tag(name='html')
    head = Tag(name='head')
    meta = Tag(name='meta')
    meta.attrs['content'] = "text/html; charset=utf-8"
    meta.attrs['http-equiv'] = "Content-Type"
    head.append(meta)

    html.append(head)
    html.append(body)

    #    fn = os.path.join(d0, 'summary.html')
    with open(fn, 'w') as f:
        f.write(str(html))

    print('Created ' + fn)


def get_branch_table(d0, project, builds, active_branches):
    branch2status = get_branch2status(builds)
    t2 = Tag(name='table')
    t2.attrs['id'] = 'tips'

    th = Tag(name='tr')
    td = Tag(name='th')
    td.append('branch name')
    th.append(td)

    td = Tag(name='th')
    td.attrs['colspan'] = 2
    td.append('last success')
    th.append(td)

    td = Tag(name='th')
    td.attrs['colspan'] = 1
    td.append('last failed build')
    th.append(td)

    t2.append(th)

    def key(x):
        if x == 'master':
            x = '00000'
        return x

    ordered = sorted(branch2status, key=key)
    for branch in ordered:
        if active_branches is not None:
            if branch not in active_branches:
                print('Not using branch %s because deleted' % branch)
                continue
        status = branch2status[branch]
        tr = Tag(name='tr')
        td = Tag(name='td')
        td.append(branch)
        tr.append(td)

        if status.last_success is not None:
            build = status.last_success

            d_build = os.path.join(d0, project, 'builds', str(build.get_build_num()))

            d_branches = os.path.join(d0, project, 'branch')
            if not os.path.exists(d_branches):
                os.makedirs(d_branches)
            d_branch = os.path.join(d_branches, path_frag_from_branch(branch))

            # print(d_branch, '->', d_build)
            if os.path.lexists(d_branch):
                os.unlink(d_branch)

            os.symlink(os.path.realpath(d_build), d_branch)

            links = Tag(name='td')
            links.attrs['class'] = 'links'
            if build.artefacts:
                links.append(get_links(build, branch))
            tr.append(links)

            author = Tag(name='span')
            avatar_url = build.get_avatar_url()

            if avatar_url is not None:
                img = Tag(name='img')
                img.attrs['class'] = 'avatar'
                img.attrs['src'] = avatar_url
                # img(a)
                author.append(img)

            td = Tag(name='td')
            td.append(author)
            td.append(build.get_subject())

            stop_time = build.get_stop_time()
            if stop_time is not None:
                td.append(' (')
                td.append(date_tag(stop_time))
                td.append(')')

            tr.append(td)

        else:
            td = Tag(name='td')

            tr.append(td)
            td = Tag(name='td')

            tr.append(td)

        if status.last_failure is not None:
            build = status.last_failure
            td = Tag(name='td')

            outcome = build.get_outcome()
            td.attrs['class'] = outcome
            stop_time = build.get_stop_time()
            if stop_time is not None:
                td.append(date_tag(stop_time))
                td.append(': ')
            a = Tag(name='a')
            a.attrs['href'] = build.get_build_url()
            a.append('#%s' % build.get_build_num())
            td.append(a)
            td.append(' ')
            td.append(build.get_outcome_string())
            tr.append(td)

        else:
            td = Tag(name='td')
            tr.append(td)

        t2.append(tr)

    return t2


def get_links(build, branch=None):
    s = Tag(name='details')
    summary = Tag(name='summary')
    summary.append('%d\xc2\xa0artefacts' % (len(build.artefacts)))
    s.append(summary)
    s.append(get_links_(build, branch))
    return s


def get_links_(build, branch=None):
    build_num = build.get_build_num()
    return get_links_from_artefacts(build.artefacts, build_num=build_num, branch=branch)


def get_links_from_artefacts(artefacts, branch=None, build_num=None):
    links = Tag(name='span')
    links.attrs['class'] = 'links'
    groups = sorted(set([art.group for art in artefacts]))
    for j, g in enumerate(groups):
        if j > 0:
            links.append(Tag(name='br'))
        tag_g = Tag(name='span')
        tag_g.attrs['class'] = 'group'
        tag_g.append(' ')
        tag_g.append(g)
        tag_g.append(Tag(name='br'))
        tag_g.append(' (')
        links.append(tag_g)

        arts = [_ for _ in artefacts if _.group == g]
        div = get_links2(arts, branch, build_num)
        links.append('(')
        links.append(div)
        links.append(')')

    return links

def get_links2(arts, branch=None, build_num=None):
    div = Tag(name='span')
    arts = reversed(sorted(arts, key=lambda _: _.display))
    for i, art in enumerate(arts):

        a = Tag(name='a')

        if art.rel is None:
            path = '#'
            a.attrs['class'] = 'not-found'
        else:
            path = art.rel
            if path is not None and branch is not None:
                path = path.replace('builds/%s' % build_num,
                                    'branch/%s' % path_frag_from_branch(branch))
        if path is not None:
            a['href'] = path
        a.append(art.display)
        if i > 0:
            div.append(' ')
        div.append(a)
    return div

def get_build_table(builds):
    table = Tag(name='table')

    th = Tag(name='tr')

    def h(s):
        td_ = Tag(name='td')
        td_.append(s)
        th.append(td_)

    h('build')
    h('commit')
    h('branch')
    h('status')
    h('')
    h('duration')
    h('results')
    h('author')
    h('commit text')

    table.append(th)
    table.attrs['id'] = 'builds'

    for build in builds.values():
        tr = Tag(name='tr')

        def f(s):
            td_ = Tag(name='td')
            td_.append(s)
            tr.append(td_)

        table.append(tr)
        outcome = build.get_outcome()
        tr.attrs['class'] = outcome

        a = Tag(name='a')
        a.attrs['class'] = 'build_url'
        a.attrs['href'] = build.get_build_url()
        a.append('#%s' % build.get_build_num())
        f(a)

        a = Tag(name='a')
        a.attrs['class'] = 'commit_url'
        a.attrs['href'] = build.get_commit_url()
        a.append(build.get_commit()[-7:])
        f(a)

        f(build.get_branch())
        f(build.get_outcome_string())
        stop_time = build.get_stop_time()
        start_time = build.get_start_time()

        duration_human = build.get_duration_human()
        if stop_time is not None:
            f(date_tag(stop_time))
        else:
            td = Tag(name='span')
            if start_time is not None:
                td.append('started ')
                td.append(date_tag(start_time))
            f(td)

        if duration_human is not None:
            f(duration_human)
        else:
            f('')

        links = Tag(name='span')
        links.attrs['class'] = 'links'
        if build.artefacts:
            links.append(get_links(build))

        f(links)

        author = Tag(name='span')
        avatar_url = build.get_avatar_url()
        author_name = build.get_author_name()
        if avatar_url is not None:
            img = Tag(name='img')
            img.attrs['class'] = 'avatar'
            img.attrs['src'] = avatar_url
            img(a)
            author.append(img)
        author.append(author_name)

        f(author)
        f(build.get_subject())

    return table


#        print('%-20s %25s %25s %20s %8s %s' % (branch, commit[-7:], outcome, name, found, fix))


def path_frag_from_branch(b):
    return b.replace('/', '-')


def date_tag(d):
    # <time class="timesince" datetime="2012-06-28T02:47:40Z">June 28, 2012</time>
    t = Tag(name='time')
    t.attrs['class'] = 'timesince'
    t.attrs['datetime'] = d.isoformat()  # + '+00:00'
    t.append(d.strftime('%Y-%m-%d %H:%M:%S'))
    return t


def parse_html(fragment):
    s = '<fragment>%s</fragment>' % fragment

    parsed = BeautifulSoup(s, 'lxml', from_encoding='utf-8')
    res = parsed.html.body.fragment
    assert res.name == 'fragment'
    return res


def collect(res, token):
    od = OrderedDict()
    for r in res:
        url = r['url'] + '?circle-token=' + token
        path = r['path']
        od[path] = url
    return od


def download_to(path, url):
    r = requests.get(url, allow_redirects=True)
    dn = os.path.dirname(path)
    if not os.path.exists(dn):
        os.makedirs(dn)
    print('Downloading %s' % path)
    with open(path, 'w') as f:
        f.write(r.content)


def duration_compact(seconds):
    seconds = int(math.ceil(seconds))
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    years, days = divmod(days, 365.242199)

    minutes = int(minutes)
    hours = int(hours)
    days = int(days)
    years = int(years)

    duration = []
    if years > 0:
        duration.append('%dy' % years)
    else:
        if days > 0:
            duration.append('%dd' % days)
        if (days < 3) and (years == 0):
            if hours > 0:
                duration.append('%dh' % hours)
            if (hours < 3) and (days == 0):
                if minutes > 0:
                    duration.append('%dm' % minutes)
                if (minutes < 3) and (hours == 0):
                    if seconds > 0:
                        duration.append('%ds' % seconds)

    return ' '.join(duration)


def locate_files(directory, pattern, followlinks=True,
                 include_directories=False,
                 include_files=True,
                 normalize=False,
                 ignore_patterns=None):
    """
        pattern is either a string or a sequence of strings
        ignore_patterns = ['*.bak']
    """
    if ignore_patterns is None:
        ignore_patterns = []

    if isinstance(pattern, str):
        patterns = [pattern]
    else:
        patterns = list(pattern)

    # directories visited
    visited = set()
    # print('locate_files %r %r' % (directory, pattern))
    filenames = []

    def matches_pattern(x):
        return any(fnmatch.fnmatch(x, _) for _ in patterns)

    def should_ignore_resource(x):
        return any(fnmatch.fnmatch(x, ip) for ip in ignore_patterns)

    def accept_dirname_to_go_inside(root_, d_):
        if should_ignore_resource(d_):
            return False
        dd = os.path.realpath(os.path.join(root_, d_))
        if dd in visited:
            return False
        visited.add(dd)
        return True

    def accept_dirname_as_match(d_):
        return include_directories and \
               not should_ignore_resource(d_) and \
               matches_pattern(d_)

    def accept_filename_as_match(fn):
        return include_files and \
               not should_ignore_resource(fn) and \
               matches_pattern(fn)

    ntraversed = 0
    for root, dirnames, files in os.walk(directory, followlinks=followlinks):
        ntraversed += 1
        dirnames[:] = [_ for _ in dirnames if accept_dirname_to_go_inside(root, _)]
        for f in files:
            if accept_filename_as_match(f):
                filename = os.path.join(root, f)
                filenames.append(filename)
        for d in dirnames:
            if accept_dirname_as_match(d):
                filename = os.path.join(root, d)
                filenames.append(filename)

    if normalize:
        real2norm = defaultdict(lambda: [])
        for norm in filenames:
            real = os.path.realpath(norm)
            real2norm[real].append(norm)
            # print('%s -> %s' % (real, norm))

        filenames = list(real2norm.keys())

    return filenames


# language=css
css = """

body {
    padding: 1em;
    font-family: Tahoma;
}

table#tips tr {
    height: 4em;
}

table#tips tr td:nth-child(3) {
    width: 20em;
    padding-left: 4em;
    padding-right: 2em;
}

table#tips tr td:nth-child(4) {
    width: 20em;
}

table#builds tr:first-child {
    font-style: italic;
}

th {
    font-style: italic;
    text-align: center;
    font-weight: normal;
}

td {
    padding-left: 1em;
    vertical-align: top;
}

td.links, span.links {
    font-size: 80%;
    min-width: 20em;
}

table#builds tr.completed_no_output td:nth-child(4), td.completed_no_output {
    color: gray;
}

table#builds tr.failed td:nth-child(4), td.failed {
    color: darkred;
    font-weight: bold;
}

table#builds tr.timedout td:nth-child(4), td.timedout {
    color: darkred;
    font-weight: bold;
}

table#builds tr.success td:nth-child(4), td.success {
    color: darkgreen;
    font-weight: bold;
}

.avatar {
    width: 1.5em;
    margin-right: 10px;

    /* position: relative; top: 0.2em;  */

    /* margin-top: -10em; */
}

a.commit_url, a.build_url {
    text-decoration: none;
    color: black;
}

a.commit_url, a.build_url {
    font-family: monospace;
}

span.group {
    display: block;
}

"""

# language=html
TEMPLATE = """

<style>CSS</style>
<script src="jquery.min.js" type="text/javascript"></script>
<script src="jquery.timesince.js" type="text/javascript"></script>

<h2>Branches </h2>

<span id='table2'/>

<h2>All builds</h2>

<p>This list is automatically generated periodically.</p>

<p>Last update: DATE</p>

<span id='table1'/>

<style>
img.avatar { width: 1em; margin-right: 10px; }
</style>

<script>
$(document).ready(function() {
    params = {refreshMs: 1000};
    $("span.timesince").timesince(params);
    $("time.timesince").timesince(params);
});
</script>

""".replace('CSS', css)

if __name__ == '__main__':
    go()
