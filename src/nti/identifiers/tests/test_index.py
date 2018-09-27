#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods

from hamcrest import is_
from hamcrest import none
from hamcrest import not_none
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_entries
from hamcrest import same_instance
from hamcrest import contains_inanyorder

import pickle
import unittest

import BTrees

import fudge

from zope import component
from zope import interface

from zope.annotation.interfaces import IAttributeAnnotatable

from zope.catalog.interfaces import ICatalog

from zope.intid.interfaces import IIntIds

from nti.coremetadata.interfaces import IUser

from nti.identifiers.index import CATALOG_NAME

from nti.identifiers.index import ValidatingSiteName
from nti.identifiers.index import ValidatingExternalTypes
from nti.identifiers.index import ValidatingExternalIdentifiers

from nti.identifiers.index import get_identifier_catalog
from nti.identifiers.index import install_identifiers_catalog

from nti.identifiers.interfaces import IUserExternalIdentityContainer

from nti.identifiers.tests import SharedConfiguringTestLayer

from nti.identifiers.utils import get_external_identifiers
from nti.identifiers.utils import get_user_for_external_id
from nti.identifiers.utils import get_external_ids_for_user


@interface.implementer(IUser, IAttributeAnnotatable)
class User(object):

    username = None

    def __init__(self, username):
        self.username = username


class TestIndex(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    @fudge.patch('nti.identifiers.utils.get_component_hierarchy_names',
                 'nti.identifiers.adapters.getSite')
    def test_index(self, mock_names, mock_adp):
        """
        Validate the index contains the correct external_ids for users.
        """
        # fake getSite()
        fake_site = fudge.Fake().has_attr(__name__='mysite')
        mock_adp.is_callable().returns(fake_site)

        # get get_component_hierarchy_names
        mock_names.is_callable().returns(['mysite'])

        # create mock users
        user1 = User(username="marko")
        user2 = User(username="ghuus")
        user3 = User(username="izabel")

        # mock intids
        class MockUtility(object):
            family = BTrees.family64

            def register(self, obj):
                pass

            def queryId(self, obj):
                if obj == user1:
                    return 1
                return 2 if user2 == obj else 3
            getId = queryId

            def getObject(self, key):
                if key == 1:
                    return user1
                return user2 if key == 2 else user3
            queryObject = getObject

        intids = MockUtility()
        component.getGlobalSiteManager().registerUtility(intids, IIntIds)

        # register
        catalog = install_identifiers_catalog(component, intids)
        assert_that(install_identifiers_catalog(component, intids),
                    is_(same_instance(catalog)))

        # now we should have it
        catalog = get_identifier_catalog()
        assert_that(catalog, not_none())

        # index nothing
        catalog.index_doc(1, user1)

        # Empty cases
        assert_that(get_user_for_external_id('type', None), none())
        assert_that(get_user_for_external_id(None, 'dneusername'), none())
        assert_that(get_user_for_external_id('type', 'dneusername'), none())

        # pylint: disable=too-many-function-args
        # One user with data
        id_container1 = IUserExternalIdentityContainer(user1)
        id_container1.add_external_mapping('TYPE1', 'ID1')
        catalog.index_doc(1, user1)
        assert_that(get_user_for_external_id('type1', 'id1'), is_(user1))
        assert_that(get_user_for_external_id('TYPE1', 'ID1'), is_(user1))

        assert_that(get_user_for_external_id('TYPE1xxx', 'ID1'), none())
        assert_that(get_user_for_external_id('TYPE1', 'ID1xxx'), none())

        # Two users
        id_container1.add_external_mapping('TYPE2', 'ID2')
        id_container2 = IUserExternalIdentityContainer(user2)
        id_container2.add_external_mapping('TYPE2', 'ID1')
        catalog.index_doc(1, user1)
        catalog.index_doc(2, user2)
        catalog.index_doc(3, user3)

        assert_that(get_user_for_external_id('type1', 'id1'), is_(user1))
        assert_that(get_user_for_external_id('type2', 'id1'), is_(user2))
        assert_that(get_user_for_external_id('type1', 'id2'), none())

        assert_that(get_user_for_external_id('TYPE1xxx', 'ID1'), none())
        assert_that(get_user_for_external_id('TYPE1', 'ID1xxx'), none())

        external_ids = get_external_ids_for_user(user1)
        assert_that(external_ids, contains_inanyorder('id1', 'id2'))

        external_ids = get_external_ids_for_user(user2)
        assert_that(external_ids, contains_inanyorder('id1'))

        external_ids = get_external_ids_for_user(user3)
        assert_that(external_ids, has_length(0))

        external_id_map = get_external_identifiers(user1)
        assert_that(external_id_map, has_entries('TYPE1', 'ID1',
                                                 'TYPE2', 'ID2'))

        external_id_map = get_external_identifiers(user2)
        assert_that(external_id_map, has_entries('TYPE2', 'ID1'))

        external_id_map = get_external_identifiers(user3)
        assert_that(external_id_map, has_length(0))

        component.getGlobalSiteManager().unregisterUtility(intids, IIntIds)
        component.getGlobalSiteManager().unregisterUtility(catalog, ICatalog,
                                                           CATALOG_NAME)

    def test_pickle(self):
        for factory in (ValidatingSiteName,
                        ValidatingExternalTypes,
                        ValidatingExternalIdentifiers):
            with self.assertRaises(TypeError):
                pickle.dumps(factory(None, None))

    @fudge.patch('nti.identifiers.utils.get_component_hierarchy_names')
    def test_coverage(self, mock_names):
        mock_names.is_callable().returns([])
        user1 = User(username="marko")
        # pylint: disable=too-many-function-args
        id_container1 = IUserExternalIdentityContainer(user1)
        id_container1.add_external_mapping('TYPE1', 'ID1')

        m = get_external_identifiers(user1)
        assert_that(m, has_length(1))
        assert_that(m, has_entries('TYPE1', 'ID1'))
