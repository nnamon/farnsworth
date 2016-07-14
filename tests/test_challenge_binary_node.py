#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from datetime import datetime, timedelta
import os
import time

from nose.tools import *
from peewee import IntegrityError

from . import setup_each, teardown_each
from farnsworth.models import (AFLJob, ChallengeBinaryNode, ChallengeSet,
                               FunctionIdentity, Round, Team)
import farnsworth.models    # to avoid collisions between Test and nosetests

NOW = datetime.now()
BLOB = "blob data"


class TestChallengeBinaryNode:
    def setup(self):
        setup_each()

    def teardown(self):
        teardown_each()

    def test_sha256_uniqueness(self):
        cs = ChallengeSet.create(name="foo")
        ChallengeBinaryNode.create(name="test1", cs=cs, blob=BLOB, sha256="same-sum")
        assert_raises(IntegrityError, ChallengeBinaryNode.create,
                      name="test1", cs=cs, blob=BLOB, sha256="same-sum")

    def test_init(self):
        cs = ChallengeSet.create(name="foo")
        cbn1 = ChallengeBinaryNode.create(name="test1", cs=cs, blob=BLOB, sha256="sum1")
        cbn2 = ChallengeBinaryNode.create(name="test1", cs=cs, blob=BLOB, sha256="sum2")
        assert_equals(cbn1.cs, cs)

    def test_root_association(self):
        cs = ChallengeSet.create(name="foo")
        root_cbn = ChallengeBinaryNode.create(name="root", cs=cs, blob=BLOB, sha256="sum1")
        cbn1 = ChallengeBinaryNode.create(name="test1", cs=cs, root=root_cbn, blob=BLOB, sha256="sum2")
        cbn2 = ChallengeBinaryNode.create(name="test2", cs=cs, root=root_cbn, blob=BLOB, sha256="sum3")

        assert_equals(cbn1.root, root_cbn)
        assert_equals(len(root_cbn.descendants), 2)
        assert_in(cbn1, root_cbn.descendants)
        assert_in(cbn2, root_cbn.descendants)

    def test_binary_is_created_and_deleted_properly(self):
        cs = ChallengeSet.create(name=str(time.time()))
        cbn = ChallengeBinaryNode.create(name="mybin", cs=cs, blob="byte data", sha256="sum1")
        binpath = cbn._path

        assert_false(os.path.isfile(binpath))
        cbn.path

        assert_true(os.path.isfile(binpath))
        assert_equals(open(cbn.path, 'rb').read(), "byte data")
        cbn = None
        # FIXME
        # assert_false(os.path.isfile(binpath))

    def test_roots(self):
        cs = ChallengeSet.create(name="foo")
        cbn1 = ChallengeBinaryNode.create(name="root1", cs=cs, blob=BLOB, sha256="sum1")
        cbn2 = ChallengeBinaryNode.create(name="root2", cs=cs, blob=BLOB, sha256="sum2")
        cbn3 = ChallengeBinaryNode.create(name="child", cs=cs, blob=BLOB, root=cbn1, sha256="sum3")

        assert_equals(len(ChallengeBinaryNode.roots()), 2)
        assert_in(cbn1, ChallengeBinaryNode.roots())
        assert_in(cbn2, ChallengeBinaryNode.roots())

    def test_all_descendants(self):
        cs = ChallengeSet.create(name="foo")
        cbn1 = ChallengeBinaryNode.create(name="root1", cs=cs, blob=BLOB, sha256="sum1")
        cbn2 = ChallengeBinaryNode.create(name="root2", cs=cs, blob=BLOB, sha256="sum2")
        cbn3 = ChallengeBinaryNode.create(name="child", cs=cs, blob=BLOB, root=cbn1, sha256="sum3")

        assert_equals(len(ChallengeBinaryNode.all_descendants()), 1)
        assert_in(cbn3, ChallengeBinaryNode.all_descendants())

    def test_submitted_and_unsubmitted_patches(self):
        r0 = Round.create(num=0, ends_at=NOW + timedelta(seconds=30))
        team = Team.create(name=Team.OUR_NAME)
        cs = ChallengeSet.create(name="foo")
        cs.rounds = [r0]
        cbn = ChallengeBinaryNode.create(name="cbn", cs=cs, sha256="sum1")
        patch1 = ChallengeBinaryNode.create(name="patch1", cs=cs, root=cbn, sha256="sum2")
        patch2 = ChallengeBinaryNode.create(name="patch2", cs=cs, root=cbn, sha256="sum3")

        assert_equals(len(cbn.unsubmitted_patches), 2)
        assert_in(patch1, cbn.unsubmitted_patches)
        assert_in(patch2, cbn.unsubmitted_patches)
        assert_equals(len(cbn.submitted_patches), 0)

        cs.submit_patches(patch1, patch2)
        assert_equals(len(cbn.submitted_patches), 2)
        assert_equals(len(cbn.unsubmitted_patches), 0)

    def test_all_tests_for_this_cb(self):
        cs = ChallengeSet.create(name="foo")
        cbn = ChallengeBinaryNode.create(name="cbn", cs=cs, blob=BLOB, sha256="sum1")
        patch1 = ChallengeBinaryNode.create(name="patch1", cs=cs, blob="data", root=cbn, sha256="sum2")
        job = AFLJob.create(cbn=cbn)
        test1 = farnsworth.models.Test.create(cbn=cbn, job=job, blob="test1")
        test2 = farnsworth.models.Test.create(cbn=cbn, job=job, blob="test2")

        assert_equals(len(patch1.tests), 0)
        assert_equals(len(patch1.all_tests_for_this_cb), 2)

    def test_found_crash_for_cb(self):
        cs = ChallengeSet.create(name="foo")
        cbn1 = ChallengeBinaryNode.create(name="cbn1", cs=cs, blob=BLOB, sha256="sum1")
        cbn2 = ChallengeBinaryNode.create(name="cbn2", cs=cs, blob=BLOB, sha256="sum2")

        job = AFLJob.create(cbn=cbn1)
        crash = farnsworth.models.Crash.create(cbn=cbn1, job=job, blob="crash", crash_pc=0x41414141)

        assert_true(cbn1.found_crash)
        assert_false(cbn2.found_crash)

    def test_symbols(self):
        cs = ChallengeSet.create(name="foo")
        cbn = ChallengeBinaryNode.create(name="cbn", cs=cs, sha256="sum1")
        identity1 = FunctionIdentity.create(cbn=cbn, address=1, symbol="aaa")
        identity2 = FunctionIdentity.create(cbn=cbn, address=2, symbol="bbb")

        assert_equals(cbn.symbols, {1: "aaa", 2: "bbb"})
