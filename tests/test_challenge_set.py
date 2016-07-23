#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from datetime import datetime
import time
import os

from nose.tools import *
from peewee import IntegrityError

from . import setup_each, teardown_each
from farnsworth.models import (AFLJob,
                               ChallengeBinaryNode,
                               ChallengeSet,
                               ChallengeSetFielding,
                               CSSubmissionCable,
                               Exploit,
                               FunctionIdentity,
                               IDSRule,
                               RexJob,
                               Round,
                               Team)
import farnsworth.models

NOW = datetime.now()
BLOB = "blob data"


class TestChallengeSet:
    def setup(self):
        setup_each()

    def teardown(self):
        teardown_each()

    def test_seen_in_round(self):
        r0 = Round.create(num=0)
        r1 = Round.create(num=1)
        cs = ChallengeSet.create(name="foo")

        cs.seen_in_round(r0)
        assert_equals(len(cs.rounds), 1)

        cs.seen_in_round(r0)
        assert_equals(len(cs.rounds), 1)

        cs.seen_in_round(r1)
        assert_equals(len(cs.rounds), 2)

    def test_fielded_in_round(self):
        now = datetime.now()
        r1 = Round.create(num=0)
        r2 = Round.create(num=1)
        cs1 = ChallengeSet.create(name="foo")
        cs1.rounds = [r1, r2]
        cs2 = ChallengeSet.create(name="bar")
        cs2.rounds = [r1]

        assert_equals(len(ChallengeSet.fielded_in_round(r1)), 2)
        assert_in(cs1, ChallengeSet.fielded_in_round(r1))
        assert_in(cs2, ChallengeSet.fielded_in_round(r1))

    def test_cbns_by_patch_type(self):
        cs = ChallengeSet.create(name="foo")
        cbn = ChallengeBinaryNode.create(name="foo", cs=cs, sha256="sum")
        cbn1 = ChallengeBinaryNode.create(name="foo1", cs=cs, patch_type="patch0", sha256="sum1")
        cbn2 = ChallengeBinaryNode.create(name="foo2", cs=cs, patch_type="patch0", sha256="sum2")
        cbn3 = ChallengeBinaryNode.create(name="foo3", cs=cs, patch_type="patch1", sha256="sum3")
        assert_in('patch0', cs.cbns_by_patch_type().keys())
        assert_in('patch1', cs.cbns_by_patch_type().keys())
        assert_in(cbn1, cs.cbns_by_patch_type()['patch0'])
        assert_in(cbn2, cs.cbns_by_patch_type()['patch0'])
        assert_in(cbn3, cs.cbns_by_patch_type()['patch1'])

    def test_submit(self):
        r1 = Round.create(num=0)
        team = Team.create(name=Team.OUR_NAME)
        cs = ChallengeSet.create(name="foo")
        cbn1 = ChallengeBinaryNode.create(name="foo", cs=cs, blob=BLOB, sha256="sum1")
        cbn2 = ChallengeBinaryNode.create(name="foo", cs=cs, blob=BLOB, sha256="sum2")

        assert_equals(len(cs.fieldings), 0)

        # Submit 2 patches at once
        cs.submit(cbns=[cbn1, cbn2], round=r1)
        assert_equals(len(cs.fieldings), 1)

        assert_equals(len(cs.fieldings.get().cbns), 2)
        assert_equals(cs.fieldings.get().team, Team.get_our())
        assert_equals(cs.fieldings.get().submission_round, Round.current_round())
        assert_is_none(cs.fieldings.get().available_round)
        assert_is_none(cs.fieldings.get().fielded_round)

        # Submit again fails
        assert_raises(IntegrityError, cs.submit, cbns=[cbn1, cbn2], round=r1)

    def test_unsubmitted_ids_rules(self):
        r1 = Round.create(num=0)
        team = Team.create(name=Team.OUR_NAME)
        cs = ChallengeSet.create(name="foo")
        ids1 = IDSRule.create(cs=cs, rules="aaa")
        ids2 = IDSRule.create(cs=cs, rules="bbb")

        assert_equals(len(cs.unsubmitted_ids_rules), 2)
        assert_in(ids1, cs.unsubmitted_ids_rules)
        assert_in(ids2, cs.unsubmitted_ids_rules)

        ids1.submit()
        assert_equals(len(cs.unsubmitted_ids_rules), 1)
        assert_not_in(ids1, cs.unsubmitted_ids_rules)
        assert_in(ids2, cs.unsubmitted_ids_rules)

        ids2.submit()
        assert_equals(len(cs.unsubmitted_ids_rules), 0)
        assert_not_in(ids1, cs.unsubmitted_ids_rules)
        assert_not_in(ids2, cs.unsubmitted_ids_rules)

    def test_unsubmitted_exploits(self):
        r1 = Round.create(num=0)
        team = Team.create(name=Team.OUR_NAME)
        cs = ChallengeSet.create(name="foo")
        cs.rounds = [r1]
        job = RexJob.create(cs=cs)
        pov1 = Exploit.create(cs=cs, job=job, pov_type='type1', exploitation_method='rop',
                              blob="exploit", c_code="exploit it")
        pov2 = Exploit.create(cs=cs, job=job, pov_type='type2', exploitation_method='rop',
                              blob="exploit", c_code="exploit it")

        assert_equals(len(cs.unsubmitted_exploits), 2)
        assert_in(pov1, cs.unsubmitted_exploits)
        assert_in(pov2, cs.unsubmitted_exploits)

        pov1.submit_to(team, 10)
        assert_equals(len(cs.unsubmitted_exploits), 1)
        assert_not_in(pov1, cs.unsubmitted_exploits)
        assert_in(pov2, cs.unsubmitted_exploits)

        pov2.submit_to(team, 10)
        assert_equals(len(cs.unsubmitted_exploits), 0)
        assert_not_in(pov1, cs.unsubmitted_exploits)
        assert_not_in(pov2, cs.unsubmitted_exploits)

    def test_cbns_original(self):
        r0 = Round.create(num=0)
        r1 = Round.create(num=1)
        our_team = Team.create(name=Team.OUR_NAME)
        other_team = Team.create(name="opponent")
        cs = ChallengeSet.create(name="foo")
        cs.rounds = [r0, r1]
        cbn = ChallengeBinaryNode.create(name="foo", cs=cs, sha256="sum1")
        cbn_patched = ChallengeBinaryNode.create(name="foo", cs=cs, patch_type="patch0", sha256="sum2")
        cbn_other_team = ChallengeBinaryNode.create(name="foo", cs=cs, sha256="sum3")
        ChallengeSetFielding.create(cs=cs, cbns=[cbn], team=our_team, available_round=r0)
        ChallengeSetFielding.create(cs=cs, cbns=[cbn_patched], team=our_team, submission_round=r0).save()
        ChallengeSetFielding.create(cs=cs, cbns=[cbn_other_team], team=other_team, available_round=r0).save()

        assert_equals(len(cs.cbns_original), 1)
        assert_in(cbn, cs.cbns_original)
        assert_not_in(cbn_patched, cs.cbns_original)
        assert_not_in(cbn_other_team, cs.cbns_original)

    def test_is_multi_cbn(self):
        r0 = Round.create(num=0)
        our_team = Team.create(name=Team.OUR_NAME)
        # CS single binary
        cs = ChallengeSet.create(name="single")
        cs.rounds = [r0]
        cbn = ChallengeBinaryNode.create(name="foo", cs=cs, sha256="sum1")
        # CS multi binary
        cs_multi = ChallengeSet.create(name="multi")
        cs_multi.rounds = [r0]
        cbn1 = ChallengeBinaryNode.create(name="foo1", cs=cs_multi, sha256="sum2")
        cbn2 = ChallengeBinaryNode.create(name="foo2", cs=cs_multi, sha256="sum3")
        # create fielding entries
        ChallengeSetFielding.create(cs=cs, cbns=[cbn], team=our_team, available_round=r0)
        ChallengeSetFielding.create(cs=cs_multi, cbns=[cbn1, cbn2], team=our_team, available_round=r0)

        assert_false(cs.is_multi_cbn)
        assert_true(cs_multi.is_multi_cbn)

    def test_all_tests_for_this_cs(self):
        cs = ChallengeSet.create(name="foo")
        job = AFLJob.create(cs=cs)
        test1 = farnsworth.models.Test.create(cs=cs, job=job, blob="test1")
        test2 = farnsworth.models.Test.create(cs=cs, job=job, blob="test2")

        assert_equals(len(cs.tests), 2)


    def test_undrilled_tests_for_cs(self):
        cs = ChallengeSet.create(name="foo")
        job = AFLJob.create(cs=cs)
        new_test = farnsworth.models.Test.create(cs=cs, job=job, blob="crash", drilled=False)

        assert_true(len(cs.undrilled_tests), 1)

    def test_found_crash_for_cs(self):
        cs = ChallengeSet.create(name="foo")
        job = AFLJob.create(cs=cs)
        crash = farnsworth.models.Crash.create(cs=cs, job=job, blob="crash", crash_pc=0x41414141)

        assert_true(cs.found_crash)

    def test_symbols(self):
        cs = ChallengeSet.create(name="foo")
        identity1 = FunctionIdentity.create(cs=cs, address=1, symbol="aaa")
        identity2 = FunctionIdentity.create(cs=cs, address=2, symbol="bbb")

        assert_equals(cs.symbols, {1: "aaa", 2: "bbb"})

    def test_unprocessed_submission_cables(self):
        cs = ChallengeSet.create(name="foo")
        cbn = ChallengeBinaryNode.create(name="foo1", cs=cs, sha256="sum")
        ids = IDSRule.create(cs=cs, rules="aaa", sha256="sum")
        cable1 = CSSubmissionCable.create(cs=cs, ids=ids, cbns=[cbn])
        cable2 = CSSubmissionCable.create(cs=cs, ids=ids, cbns=[])

        assert_equals(len(cs.unprocessed_submission_cables()), 2)
        assert_equals(cable1, cs.unprocessed_submission_cables()[0])
        assert_equals(cable2, cs.unprocessed_submission_cables()[1])

        cable1.process()
        assert_equals(len(cs.unprocessed_submission_cables()), 1)

    def test_has_submissions_in_round(self):
        r0 = Round.create(num=0)
        r1 = Round.create(num=1)
        cs = ChallengeSet.create(name="foo")
        cbn = ChallengeBinaryNode.create(name="foo1", cs=cs, sha256="sum")
        our_team = Team.create(name=Team.OUR_NAME)
        other_team = Team.create(name="enemy")

        ChallengeSetFielding.create(cs=cs, cbns=[cbn], team=our_team, submission_round=r1)
        assert_false(cs.has_submissions_in_round(r0))
        assert_true(cs.has_submissions_in_round(r1))

        ChallengeSetFielding.create(cs=cs, cbns=[cbn], team=other_team, submission_round=r0)
        assert_false(cs.has_submissions_in_round(r0))

        ChallengeSetFielding.create(cs=cs, cbns=[cbn], team=our_team, submission_round=r0)
        assert_true(cs.has_submissions_in_round(r0))

    def test_most_reliable_exploit(self):
        r1 = Round.create(num=0)
        team = Team.create(name=Team.OUR_NAME)
        cs = ChallengeSet.create(name="foo")
        cs.rounds = [r1]
        job1 = RexJob.create(cs=cs)
        job2 = RexJob.create(cs=cs)
        job3 = RexJob.create(cs=cs)
        job4 = RexJob.create(cs=cs)

        pov1 = Exploit.create(cs=cs, job=job1, pov_type='type1', exploitation_method='rop',
                              blob="exploit1", c_code="exploit it", reliability=0.9)
        assert_equals(pov1, cs.most_reliable_exploit)

        pov2 = Exploit.create(cs=cs, job=job2, pov_type='type2', exploitation_method='rop',
                              blob="exploit2", c_code="exploit it", reliability=0.5)
        assert_equals(pov1, cs.most_reliable_exploit)

        pov3 = Exploit.create(cs=cs, job=job3, pov_type='type2', exploitation_method='rop',
                              blob="exploit3", c_code="exploit it", reliability=0.9)
        assert_equals(pov1, cs.most_reliable_exploit)

        pov4 = Exploit.create(cs=cs, job=job4, pov_type='type2', exploitation_method='rop',
                              blob="exploit4", c_code="exploit it", reliability=1.0)
        assert_equals(pov4, cs.most_reliable_exploit)
