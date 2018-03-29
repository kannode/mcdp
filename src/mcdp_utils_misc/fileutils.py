# -*- coding: utf-8 -*-
import codecs
from contextlib import contextmanager
import os
import shutil
from tempfile import mkdtemp, NamedTemporaryFile

from compmake.utils import friendly_path, make_sure_dir_exists
from .path_utils import expand_all


def get_mcdp_tmp_dir():
    """ Returns *the* temp dir for this project.
	Note that we need to customize with username, otherwise
	there will be permission problems.  """
    from tempfile import gettempdir
    d0 = gettempdir()
    import getpass
    username = getpass.getuser()
    d = os.path.join(d0, 'mcdp_tmp_dir-%s' % username)
    if not os.path.exists(d):
        try:
            os.makedirs(d)
        except OSError:
            pass
    return d


def create_tmpdir(prefix='tmpdir'):
    mcdp_tmp_dir = get_mcdp_tmp_dir()
    d = mkdtemp(dir=mcdp_tmp_dir, prefix=prefix)
    return d


@contextmanager
def tmpdir(prefix='tmpdir', erase=True, keep_on_exception=False):
    ''' Yields a temporary dir that shall be deleted later.

        If keep_on_exception is True, does not erase.
        This is helpful for debugging problems.
     '''
    d = create_tmpdir(prefix)
    try:
        yield d
    except:
        if erase and (not keep_on_exception):
            shutil.rmtree(d)
        raise
    if erase:
        shutil.rmtree(d)


@contextmanager
def tmpfile(suffix):
    ''' Yields the name of a temporary file '''
    temp_file = NamedTemporaryFile(suffix=suffix)
    yield temp_file.name
    temp_file.close()


def read_data_from_file(filename):
    if not os.path.exists(filename):
        if os.path.lexists(filename):
            msg = 'The link %s does not exist.' % filename
            msg += ' it links to %s' % os.readlink(filename)
            raise ValueError(filename)
        else:
            msg = 'Could not find file %r' % filename
            msg += ' from directory %s' % os.getcwd()
            raise ValueError(filename)
    with open(filename) as f:
        return f.read()


def read_file_encoded_as_utf8(filename):
    u = codecs.open(filename, encoding='utf-8').read()
    s = u.encode('utf-8')
    return s


def write_data_to_file(data, filename, quiet=False):
    """
        Writes the data to the given filename.
        If the data did not change, the file is not touched.

    """
    from mcdp import logger
    if not isinstance(data, str):
        msg = 'Expected "data" to be a string, not %s.' % type(data).__name__
        raise ValueError(msg)
    if len(filename) > 256:
        msg = 'Invalid argument filename: too long. Did you confuse it with data?'
        raise ValueError(msg)

    filename = expand_all(filename)
    make_sure_dir_exists(filename)

    if os.path.exists(filename):
        current = open(filename).read()
        if current == data:
            if not 'assets' in filename:
                logger.debug('already up to date %s' % friendly_path(filename))
            return

    with open(filename, 'w') as f:
        f.write(data)

    if not quiet:
        logger.debug('Written to: %s' % friendly_path(filename))

