# -*- coding: utf-8 -*-

from mcdp import MCDPConstants

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
