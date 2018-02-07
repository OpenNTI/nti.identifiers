#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods

from hamcrest import is_
from hamcrest import assert_that

import unittest

import fudge

from nti.identifiers.adapters import ExternalIdentityContainer
from nti.identifiers.adapters import UserExternalIdentityValidator

from nti.identifiers.interfaces import MultipleUserExternalIdentitySitesError

from nti.identifiers.tests import SharedConfiguringTestLayer


class TestAdpters(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    @fudge.patch('nti.identifiers.adapters.getSite')
    def test_multiple_sites(self, mock_adp):
        fake_site = fudge.Fake().has_attr(__name__='mysite')
        mock_adp.is_callable().returns(fake_site)

        container = ExternalIdentityContainer()
        container.site_name = u'myother'

        with self.assertRaises(MultipleUserExternalIdentitySitesError):
            container.add_external_mapping('x', 'y')

    def test_validator(self):
        validator = UserExternalIdentityValidator(None)
        assert_that(validator.is_valid(None, None),
                    is_(False))
