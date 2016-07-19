#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from datetime import datetime
import os

from peewee import FixedCharField, ForeignKeyField

from .base import BaseModel
from .ids_rule import IDSRule
from .round import Round
from .team import Team

"""IDSRuleFielding model"""


class IDSRuleFielding(BaseModel):
    """IDSRuleFielding model"""

    ids_rule = ForeignKeyField(IDSRule, related_name='fieldings')
    team = ForeignKeyField(Team, related_name='ids_fieldings')
    submission_round = ForeignKeyField(Round, related_name='ids_fieldings', null=True)
    available_round = ForeignKeyField(Round, related_name='ids_fieldings', null=True)
    fielded_round = ForeignKeyField(Round, related_name='ids_fieldings', null=True)
    sha256 = FixedCharField(max_length=64, null=True) # FIXME