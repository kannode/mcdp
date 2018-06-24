# -*- coding: utf-8 -*-
from collections import namedtuple

from mcdp import MCDPConstants

LinkInfo = namedtuple('LinkInfo', 'id2filename main_headers')

from .logs import logger
from .mcdp_render import mcdp_render_main
from .mcdp_render_manual import mcdp_render_manual_main
from .pipeline import render_complete

if True:
    import git.cmd

    git.cmd.log.disabled = True

if MCDPConstants.softy_mode:
    import getpass

    if getpass.getuser() == 'andrea':
        logger.error('Remember this might break MCDP')


# All of these are for Cython who has problems pickling
from .source_info_imp import SourceInfo, HeaderIdent, Author
from .elements_abbrevs import Result
from .html_links import GenericReference
from .videos import VimeoInfo
from .github_file_ref.reference import GithubFileRef
from .manual_join_imp import DocToJoin
from .sync_from_circle import Artefact
from .tocs import LinkElement
