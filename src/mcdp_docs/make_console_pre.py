# -*- coding: utf-8 -*-
from collections import namedtuple

from bs4.element import NavigableString, Tag
from contracts import contract
from mcdp import MCDPConstants
from mcdp_utils_xml import add_class, has_class

# What is recognized as a program name
programs = ['sudo', 'pip', 'git', 'python', 'cd', 'apt-get', 'rosrun',
            'echo', 'sync', 'tee', 'curl', 'rm', 'df', 'ls',
            'catkin_make', 'ntpdate', 'groups', 'which',
            'what-the-duck', 'wajig', 'dpigs',
            'adduser', 'useradd', 'passwd', 'chsh',
            'rostopic', 'roscd', 'rviz', 'rqt_console',
            'apt-mark', 'iwconfig', 'vcgencmd', 'hostname',
            'mcdp-web', 'mcdp-solve', 'mcdp-render', 'npm',
            'mcdp-plot', 'mcdp-eval', 'mcdp-render-manual',
            'dd', 'apt', 'ifconfig', 'iconfig', 'htop',
            'iotop', 'iwlist', 'git-ignore', 'sha256sum', 'umount', 'mount', 'xz',
            'raspi-config', 'usermod', 'udevadm', 'sh', 'apt-key', 'systemctl',
            'mkswap', 'swapon', 'visudo', 'update-alternatives',
            'mkdir', 'chmod', 'wget', 'byobu-enable', 'exit', 'ssh', 'scp', 'rsync',
            'raspistill', 'reboot', 'vim', 'vi', 'ping', 'ssh-keygen',
            'mv', 'cat', 'touch', 'source', 'make', 'roslaunch', 'jstest',
            'shutdown', 'virtualenv', 'nodejs', 'cp', 'fc-cache', 'venv',
            'add-apt-repository', 'truncate', 'losetup', 'gparted',
            'rosbag', 'roscore',
            'export', 'fdisk', 'rosdep', 'rosrun', 'rosparam', 'rospack',
            'rostest'] \
           + ['|']  # pipe

program_commands = []

ConsoleLine = namedtuple('ConsoleLine', 'hostname symbol command')


@contract(returns='$ConsoleLine|None')
def is_console_line(line):
    """ Returns true if it looks like a console line, such as:

        $ command args
        hostname $ command args
        hostname # command args
    """

    def is_console_token(x):
        return x in ['$', 'DOLLAR']

    tokens = line.strip().split(' ')
    if not tokens:
        return None
    if is_console_token(tokens[0]):
        hostname = None
        symbol = tokens[0]
        command = " ".join(tokens[1:])

    elif len(tokens) >= 2 and is_console_token(tokens[1]):
        hostname = tokens[0]
        symbol = tokens[1]
        command = " ".join(tokens[2:])

    else:
        return None

    return ConsoleLine(hostname=hostname, symbol=symbol, command=command)


def mark_console_pres(soup, res, location):
    mark_console_pres_highlight(soup, res, location)
    mark_console_pres_defaults(soup, res, location)
    link_to_command_explanation(soup, res, location)


#     if 'program' in str(soup):
#         if not '<a ' in str(soup):
#             print str(soup)
#             raise Exception(str(soup))


def link_to_command_explanation(soup, res, location):
    """
        Looks for

            pre.console span.program

        and creates a link to the section.
    """

    for s in soup.select('span'):
        if has_class(s, 'program'):
            #             logger.debug('found command: %s' % s)
            program_name = list(s.children)[0]
            a = Tag(name='a')
            add_class(a, MCDPConstants.CLASS_IGNORE_IF_NOT_EXISTENT)
            a.attrs['href'] = '#' + program_name
            a.append(s.__copy__())
            s.replace_with(a)


def mark_console_pres_defaults(soup, res, location):
    """
        Looks in "pre code" or "p code" blocks
        and changes a pattern of the type

            xxxx ![variable] xxxx

        into
            xxxx <span class='placeholder'>variable</span>
    """

    for code in soup.select('code'):
        join_successive_strings(code)

        replace_template(code, res, location)


def replace_template(element, res, location):
    for t in element.children:
        if isinstance(t, NavigableString):
            if MCDPConstants.placeholder_marker_start is not None:
                if MCDPConstants.placeholder_marker_start in t:
                    process_ns(t, res, location)
        else:
            replace_template(t, res, location)


def join_successive_strings(e):
    """ Joins successive strings in a BS4 element """
    children = list(e.children)
    for i in range(len(children) - 1):
        #         print(' %s %s %s' % (i, type(children[i]), type(children[i+1])))
        if isinstance(children[i], NavigableString) and \
                isinstance(children[i + 1], NavigableString):
            #             print('collapsed %r and %r' % (children[i], children[i+1]))
            both = children[i] + children[i + 1]
            children[i].replace_with(both)
            children[i + 1].extract()
            join_successive_strings(e)
            return


def process_ns(t, res, location):
    s = t + ''

    marker = MCDPConstants.placeholder_marker_start
    marker2 = MCDPConstants.placeholder_marker_end
    if marker not in s:
        return



    i = s.index(marker)
    try:
        n = i + s[i:].index(marker2)
    except ValueError:
        msg = 'I found the substring "%s" and so I thought there would ' % marker
        msg += 'be a closing "%s"; however, I could not find one.' % marker2
        msg += '\n\nIn string: %r.' % s
        msg += '\n\nAbove: %s' % t.parent
        # logger.warning(msg)
        # logger.warning(
        # logger.warning('Above: %s' % t.parent)
        res.note_error(msg, location)
        return

    before = s[:i]
    inside = s[i + len(marker):n]
    after = s[n + len(marker2):]
    #     logger.debug('before = %r inside = %r after = %r' % (before, inside, after))

    p = Tag(name='span')
    p.attrs['class'] = 'placeholder'
    p.append(inside)
    t.replace_with(p)
    p.insert_before(before)
    p.insert_after(after)


def mark_console_pres_highlight(soup, res, location):
    for code in soup.select('pre code'):
        pre = code.parent
        if code.string is None:
            continue
        s0 = code.string

        from HTMLParser import HTMLParser
        h = HTMLParser()
        s = h.unescape(s0)
        if s != s0:
            #             print('decoded %r -> %r' % (s0, s))
            pass

        beg = s.strip()

        # is it a console line?
        ct = is_console_line(beg)

        if ct is None:
            continue

        add_class(pre, 'console')

        # add class "on-hostname"
        if ct.hostname is not None:
            cn = 'on-%s' % str(ct.hostname)
            add_class(pre, cn)

        code.string = ''

        lines = s.split('\n')

        def is_program(x, l):
            if x == 'git' and 'apt' in l:
                return False
            return x in programs

        for j, line in enumerate(lines):
            tokens = line.split(' ')
            for i, token in enumerate(tokens):
                previous_is_sudo_or_dollar = i >= 1 and tokens[i - 1] in ['$', 'sudo']

                if token in ['$', 'DOLLAR']:
                    # add <span class=console_sign>$</span>
                    e = Tag(name='span')
                    e['class'] = 'console_sign'
                    e.string = '$'
                    code.append(e)
                elif i == 0 and token == ct.hostname:
                    # it's the hostname
                    e = Tag(name='span')
                    e['class'] = 'hostname'
                    e.string = token
                    code.append(e)
                elif is_program(token, line) and previous_is_sudo_or_dollar:
                    e = Tag(name='span')
                    e['class'] = '%s program' % token
                    e.string = token
                    code.append(e)
                elif token in program_commands:
                    e = Tag(name='span')
                    e['class'] = '%s program_command' % token
                    e.string = token
                    code.append(e)
                elif token and token[0] == '-':
                    e = Tag(name='span')
                    e['class'] = 'program_option'
                    e.string = token
                    code.append(e)
                else:
                    code.append(NavigableString(token))

                is_last = i == len(tokens) - 1
                if not is_last:
                    before = '![' in ' '.join(tokens[:i + 1])
                    if not before:
                        # XXX: this is a bug
                        space = Tag(name='span')
                        space.append(' ')
                        space['class'] = 'space'
                        code.append(space)
                    else:
                        code.append(' ')

            is_last_line = j == len(lines) - 1
            if not is_last_line:
                code.append(NavigableString('\n'))
