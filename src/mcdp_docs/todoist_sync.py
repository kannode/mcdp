import pickle
import time

from mcdp_utils_misc import get_md5

from mcdp_docs.location import GithubLocation

from mcdp_docs.manual_constants import MCDPManualConstants

from mcdp_docs import logger
import tomd

def todoist_sync(data, user, secret, prefix):
    import todoist
    api = todoist.TodoistAPI()
    api.user.login(user, secret)

    response = api.sync()
    if 'error' in response:
        print response
        raise Exception(response['error_extra'])
    projects = api.projects.all()
    # print projects
    use = 'Duckuments Tasks'
    for p in projects:
        if p['name'] == use:
            project_id = p['id']
            break
    else:
        msg = 'Could not find project %r' % use
        msg += '\nAvailable: %s' % ", ".join((_['name'] for _ in projects))
        raise Exception(msg)

    collaborators = response['collaborators']
    for c in collaborators:
        print c['full_name'], c['email']

    items = [_ for _ in  api.items.all() if _['project_id'] == project_id]
    found = {}
    for i in items:
        if ';' in i['content']:
            tokens = i['content'].split(';')
            found[tokens[1].strip()] = i


    tasks = data.get_notes_by_tag(MCDPManualConstants.NOTE_TAG_TASK)
    n = 0
    for task in tasks:

        ID = get_md5(str(task.msg))[-8:]
        if ID in found:
            msg = 'Task %s already in DB' % ID
            logger.info(msg)

            item = found[ID]
            if item['checked']:
                logger.debug('Setting the item to not done.')
                api.items.uncomplete([item])

            continue

        responsible_uid = get_task_person_uid(task, collaborators)

        html = task.as_html()
        for img in list(html.select('img')):
            img.extract()
        for a in html.select('a[href]'):
            href = a.attrs['href']
            if not href.startswith('http'):
                href = prefix + href
                a.attrs['href'] = href

        html_str = str(html)
        html_str = html_str.replace('<br/>',' ')
        res = tomd.Tomd(html_str).markdown

        location = list(task.locations.values())[0]
        stack = location.get_stack()
        for l in stack:
            if isinstance(l, GithubLocation):
                head = l.path
                break
        else:
            head = '???'

        content = head + '; ' + ID
        # content = res[:100]
        item = api.items.add(content, project_id, responsible_uid=responsible_uid)
        api.notes.add(item['id'], res)

        n += 1
        print content
        if n > 45:
            break

        time.sleep(0.2)

    print api.commit()
    print api.sync()

def get_task_person_uid(task, collaborators):
    name = get_task_person(task)
    if name == 'Liam Paull':
        name = 'Liam'
    if name == 'Kirsten Bowser':
        name = 'Anne Kirsten Bowser'
    # name = 'Andrea Censi'
    try:
        return get_uid(name, collaborators)
    except KeyError:
        logger.debug('cannot find name %r' % name)

        return None

def get_uid(name, collaborators):
    for c in collaborators:
        if c['full_name'] == name:
            return c['id']
    raise KeyError(name)

def get_task_person(task):
    tags = task.tags
    for t in tags:
        if t.startswith('for:'):
            return t[4:]
    return None

def todoist_sync_main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--actually", help="Actually do it", action="store_true")

    parser.add_argument("--user", help="User name", required=True)
    parser.add_argument("--secret", help="User secret", required=True)
    parser.add_argument("--tasks", help="filename", required=True)
    parser.add_argument("--prefix", help="prefix", required=True)

    args = parser.parse_args()
    for_real = args.actually
    if for_real:
        print('actually doing it')
    else:
        print('dry-run')

    user = args.user
    secret = args.secret

    logger.info('user: %r' % user)
    logger.info(' pwd: %r' % secret)
    data = pickle.loads(open(args.tasks).read())
    print data

    todoist_sync(data, user=user, secret=secret, prefix=args.prefix)


if __name__ == '__main__':
    todoist_sync_main()
