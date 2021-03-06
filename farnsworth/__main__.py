#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Setup farnsworth"""

from __future__ import unicode_literals, absolute_import

import sys

import farnsworth.log
LOG = farnsworth.log.LOG.getChild('main')

import farnsworth.config
from . import create_tables, drop_tables


def main(args=None):
    """Run farnsworth setup."""
    if args is None:
        args = sys.argv

    if args[1:]:
        if args[1] == 'create':
            LOG.debug("Setting up database tables")
            create_tables()
            return 0
        elif args[1] == 'drop':
            LOG.debug("Dropping database tables")
            drop_tables()
            return 0

if __name__ == '__main__':
    sys.exit(main())
