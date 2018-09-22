import argparse
import datetime
from collections import OrderedDict, namedtuple

import pytz
import ruamel.yaml as yaml
from bs4 import Tag
from contracts import check_isinstance

from mcdp_cli import mkdirs_thread_safe
from mcdp_utils_misc import write_data_to_file
from mcdp_utils_xml import bs
from .sync_from_circle import sync_from_circle_main_actual, date_tag, get_branch2status, path_frag_from_branch

RepoRef = namedtuple('RepoRef', 'org name')


class BookShelf(object):
    def __init__(self, groups, header, footer, head):
        self.groups = groups
        self.header = header
        self.footer = footer
        self.head = head

    @staticmethod
    def from_yaml(data):
        bgs = OrderedDict()
        check_isinstance(data, dict)
        # print data.__repr__()
        for k, v in data['groups'].items():
            bgs[k] = BookGroup.from_yaml(k, v)
        header = data.get('header', '')
        head = data.get('head', '')
        footer = data.get('footer', '')
        return BookShelf(bgs, header, footer, head)

    @staticmethod
    def from_file(fn):
        data_s = open(fn).read()

        data = yaml.load(data_s, Loader=yaml.RoundTripLoader)
        return BookShelf.from_yaml(data)

    def __repr__(self):
        return "BookShelf(%s)" % self.groups


class BookGroup(object):
    def __init__(self, group_id, books, title, abstract):
        self.group_id = group_id
        self.books = books
        self.title = title
        self.abstract = abstract

    def __repr__(self):
        return "BookGroup(%s, %s)" % (self.title, self.books)

    @staticmethod
    def from_yaml(k, data):
        check_isinstance(data, dict)
        books = OrderedDict()
        for k, v in data['books'].items():
            books[k] = Book.from_yaml(k, v)

        title = data['title']
        abstract = data.get('abstract', None)
        return BookGroup(k, books, title, abstract)


class Book(object):
    def __init__(self, book_id, repo, title, abstract):
        self.book_id = book_id
        self.repo = repo
        self.title = title
        self.abstract = abstract

    def __repr__(self):
        return "Book(%s, %s)" % (self.title, self.repo)

    @staticmethod
    def from_yaml(k, data):
        repo = data.get('repo', None)
        if repo:
            tokens = repo.split('/')
            org = tokens[0]
            name = tokens[1]
            repo = RepoRef(org, name)

        abstract = data.get('abstract', None)
        title = data['title']
        return Book(k, repo, title, abstract)


# !!omap
# - base:
#     title: Information about the project
#
#     abstract: |
#         This is general information about the project
#         and how to contribute to it.
#
#     books: !!omap
#
#         - the_duckietown_project:
#             repo: duckietown/docs-the_duckietown_project
#             title: The Duckietown Project
#             abstract: |
#                 Learn about the history and current status.


import os


def sync_circle_multiple_main():
    parser = argparse.ArgumentParser(description='Ping the swarm')
    parser.add_argument('--books', type=str, help='books.yaml', required=True)
    parser.add_argument('--base', type=str, required=True)
    parser.add_argument('--limit', type=int, default=3)
    parser.add_argument('--dry', action='store_true')

    parsed = parser.parse_args()
    base = parsed.base
    limit = parsed.limit

    bshelf = BookShelf.from_file(parsed.books)

    html = get_base_doc()
    table = Tag(name='table')
    table.attrs['id'] = 'maintable'
    downloads_base = os.path.join(base, 'downloads')
    mkdirs_thread_safe(downloads_base)
    mkdirs_thread_safe(base)

    section = Tag(name='section')
    section.append(table)

    for bg_id, bg in bshelf.groups.items():
        if not bg.books:
            continue
        tr = Tag(name='tr')
        tr.attrs['class'] = 'group'
        td = Tag(name='td')
        td.attrs['colspan'] = 3
        td.append(bg.title)
        tr.append(td)
        table.append(tr)
        table.append('\n')
        for bk_id, bk in bg.books.items():
            if bk.repo:
                username, project = bk.repo
                # d0 = os.path.join(base, bk_id)
                # mkdirs_thread_safe(d0)
                fn_rel = os.path.join('downloads', bk_id, 'branches.html')
                fn = os.path.join(base, fn_rel)

                outd = os.path.join(base, bk_id)
                outd_target = os.path.join('downloads', bk_id, project, 'branch', 'master', bk_id)
                # print('%r %r' % (outd, outd_target))
                if os.path.lexists(outd):
                    os.unlink(outd)
                    # os.chdir(os.path.join(base, bk_id))
                    # print('creating link  in %s' % os.getcwd())
                os.symlink(outd_target, outd)

                if not parsed.dry:

                    ci = sync_from_circle_main_actual(username, project,
                                                      os.path.join(downloads_base, bk_id),
                                                      fn, repo=None, limit=limit)
                    builds = ci.builds
                    active_branches = ci.active_branches
                else:
                    builds = {}
                    active_branches = None

                tr = Tag(name='tr')
                tr.append('\n')
                #
                # td = Tag(name='td')
                # td.attrs['class'] = 'repo'
                # td.append(project)
                # tr.append(td)

                td = Tag(name='td')
                td.attrs['class'] = 'title'
                a = Tag(name='a')

                a.attrs['href'] = os.path.join(bk_id, 'out', 'index.html')

                a.append(bk.title or "???")

                td.append(a)
                tr.append(td)
                tr.append('\n')

                td = Tag(name='td')
                td.attrs['class'] = 'repo'
                a = Tag(name='a')
                a.attrs['href'] = 'http://github.com/%s/%s' % (username, project)
                # a.append(u'⚙')
                # a.append("&#9881;")
                a.append(u"")
                a.attrs['class'] = 'fa fa-fw fa-github'
                a.append('')
                td.append(a)
                tr.append(td)
                tr.append('\n')

                td = Tag(name='td')
                td.attrs['class'] = 'builds'

                a = Tag(name='a')

                a.attrs['href'] = fn_rel
                # a.attrs['class'] = 'fa fa-fw fa-history'
                # a.append(u'⚙')
                # a.append("&#9881;")
                # a.append(u"\u2699")
                a.append("builds")
                td.append(a)
                tr.append(td)
                tr.append('\n')

                td = Tag(name='td')

                if builds:
                    branch2status = get_branch2status(builds)

                    t = Tag(name='table')
                    for branch, status in branch2status.items():
                        if active_branches and not branch in active_branches:
                            continue
                        last_build = status.builds[0]
                        t_tr = Tag(name='tr')

                        t_tr_td = Tag(name='td')
                        t2 = Tag(name='a')
                        t2.attrs['class'] = [last_build.get_outcome(), 'branch-indicator']
                        t2.append(str(last_build.get_build_num()))
                        t2.attrs['href'] = last_build.get_build_url()
                        t_tr_td.append(t2)
                        t_tr.append(t_tr_td)

                        t_tr_td = Tag(name='td')
                        img = Tag(name='img')
                        img.attrs['src'] = last_build.get_avatar_url()
                        img.attrs['style'] = 'width: 16px'
                        t_tr_td.append(img)
                        t_tr.append(t_tr_td)

                        t_tr_td = Tag(name='td')
                        a = Tag(name='a')
                        a.attrs['class'] = [last_build.get_outcome(), 'branch-indicator']
                        a.append(branch)
                        if last_build.artefacts:
                            p = os.path.join('downloads', bk_id, project, 'branch', path_frag_from_branch(branch),
                                             bk_id, 'out', 'index.html')
                            a['href'] = p
                        t_tr_td.append(a)
                        # if last_build.artefacts:
                        #     t_tr_td.append(get_links(last_build, branch))
                        t_tr.append(t_tr_td)

                        # t_tr_td = Tag(name='td')
                        # if last_build.artefacts:
                        #     t_tr_td.append(get_links(last_build, branch))
                        # t_tr.append(t_tr_td)

                        t_tr_td = Tag(name='td')
                        when = last_build.get_stop_time()
                        t_tr_td.append(date_tag(when))
                        t_tr.append(t_tr_td)

                        t.append(t_tr)
                    td.append(t)

                tr.append(td)

                table.append(tr)
                table.append('\n')

    now = datetime.datetime.now(tz=pytz.utc)
    section.append(date_tag(now))

    html.body.append(section)

    header = bs(bshelf.header)
    html.head.insert(0, header)

    footer = bs(bshelf.footer)
    html.body.append(footer)

    head = bs(bshelf.head)
    html.head.append(head)

    summary = os.path.join(base, 'index.html')
    write_data_to_file(str(html), summary)


CSS = """


"""


def get_base_doc():
    html = Tag(name='html')
    head = Tag(name='head')
    meta = Tag(name='meta')
    meta.attrs['content'] = "text/html; charset=utf-8"
    meta.attrs['http-equiv'] = "Content-Type"
    #
    # stylesheet = 'v_manual_split'
    # link = Tag(name='link')
    # link['rel'] = 'stylesheet'
    # link['type'] = 'text/css'
    # # link['href'] = get_css_filename('compiled/%s' % stylesheet)
    # head.append(link)

    style = Tag(name='style')

    style.append(CSS)

    head.append(style)
    head.append(meta)
    body = Tag(name='body')

    html.append("\n")
    html.append(head)
    html.append("\n")
    html.append(body)
    html.append("\n")
    return html


if __name__ == '__main__':
    sync_circle_multiple_main()
