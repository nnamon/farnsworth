#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from .config import master_db
from .log import LOG

"""Farnsworth database setup."""


def tables():
    from farnsworth.models import (Bitmap,
                                   CBPollPerformance,
                                   ChallengeBinaryNode,
                                   ChallengeSet,
                                   ChallengeSetFielding,
                                   Crash,
                                   Evaluation,
                                   Exploit,
                                   ExploitFielding,
                                   Feedback,
                                   FunctionIdentity,
                                   FuzzerStat,
                                   IDSRule,
                                   IDSRuleFielding,
                                   Job,
                                   PatchScore,
                                   Pcap,
                                   PovTestResult,
                                   RawRoundPoll,
                                   RawRoundTraffic,
                                   RopCache,
                                   Round,
                                   Score,
                                   Team,
                                   Test,
                                   TesterResult,
                                   TracerCache,
                                   ValidPoll)
    models = [Bitmap,
              CBPollPerformance,
              ChallengeBinaryNode,
              ChallengeSet,
              ChallengeSetFielding,
              Crash,
              Evaluation,
              Exploit,
              ExploitFielding,
              Feedback,
              FunctionIdentity,
              FuzzerStat,
              IDSRule,
              IDSRuleFielding,
              Job,
              PatchScore,
              Pcap,
              PovTestResult,
              RawRoundPoll,
              RawRoundTraffic,
              RopCache,
              Round,
              Score,
              Team,
              Test,
              TesterResult,
              TracerCache,
              ValidPoll]
    through_models = [ChallengeSet.rounds,
                      ChallengeSetFielding.cbns]
    return models + [tm.get_through_model() for tm in through_models]

def create_tables():
    LOG.debug("Creating tables...")
    master_db.create_tables(tables(), safe=True)

    from farnsworth.models import (ChallengeBinaryNode,
                                   ChallengeSetFielding)
    master_db.create_index(ChallengeBinaryNode, ['sha256'], unique=True)
    master_db.create_index(ChallengeSetFielding, ['cs', 'team', 'submission_round'], unique=True)
    master_db.create_index(ChallengeSetFielding, ['cs', 'team', 'available_round'], unique=True)
    master_db.create_index(ChallengeSetFielding, ['cs', 'team', 'fielded_round'], unique=True)

def drop_tables():
    LOG.debug("Dropping tables...")
    master_db.drop_tables(tables(), safe=True, cascade=True)
