from django.test import TestCase
from django.contrib.auth.models import Group, User
from django.db.models.signals import post_save, post_delete, m2m_changed, post_migrate
from cities_light.models import City, Country
from pinax.notifications.models import NoticeType

from meetup.constants import COMMUNITY_MEMBER, COMMUNITY_MODERATOR
from meetup.models import MeetupLocation
from meetup.signals import (manage_meetup_location_groups, remove_meetup_location_groups,
                            add_meetup_location_members, add_meetup_location_moderators,
                            delete_meetup_location_members, delete_meetup_location_moderators,
                            create_notice_types)
from users.models import SystersUser


class SignalsTestCase(TestCase):
    def setUp(self):
        post_save.connect(manage_meetup_location_groups, sender=MeetupLocation,
                          dispatch_uid="manage_groups")
        post_delete.connect(remove_meetup_location_groups, sender=MeetupLocation,
                            dispatch_uid="remove_groups")
        m2m_changed.connect(add_meetup_location_members, sender=MeetupLocation.members.through,
                            dispatch_uid="add_members")
        m2m_changed.connect(add_meetup_location_moderators,
                            sender=MeetupLocation.moderators.through,
                            dispatch_uid="add_moderators")
        m2m_changed.connect(delete_meetup_location_members, sender=MeetupLocation.members.through,
                            dispatch_uid="delete_members")
        m2m_changed.connect(delete_meetup_location_moderators,
                            sender=MeetupLocation.moderators.through,
                            dispatch_uid="delete_moderators")
        post_migrate.connect(create_notice_types, dispatch_uid="create_notice_types")
        self.password = "foobar"

    def test_manage_meetup_location_groups(self):
        """Test addition of groups when saving a Meetup Location object"""
        user = User.objects.create_user(username='foo', password=self.password,
                                        email='user@test.com')
        systers_user = SystersUser.objects.get(user=user)
        country = Country.objects.create(name='Bar', continent='AS')
        location = City.objects.create(name='Baz', display_name='Baz', country=country)
        meetup_location = MeetupLocation.objects.create(    # noqa
            name="Foo", slug="foo", location=location,
            description="It's a test meetup location", leader=systers_user)
        groups_count = Group.objects.count()
        self.assertEqual(groups_count, 3)

    def test_remove_community_groups(self):
        """Test the removal of groups when a Meetup Location is deleted"""
        user = User.objects.create_user(username='foo', password=self.password,
                                        email='user@test.com')
        systers_user = SystersUser.objects.get(user=user)
        country = Country.objects.create(name='Bar', continent='AS')
        location = City.objects.create(name='Baz', display_name='Baz', country=country)
        meetup_location = MeetupLocation.objects.create(
            name="Foo", slug="foo", location=location,
            description="It's a test meetup location", leader=systers_user)
        groups_count = Group.objects.count()
        self.assertEqual(groups_count, 3)
        meetup_location.delete()
        groups_count = Group.objects.count()
        self.assertEqual(groups_count, 0)

    def test_add_meetup_location_members(self):
        """Test addition of permissions to a user when she is made a meetup location member"""

        user = User.objects.create(username='foo', password=self.password)
        systers_user = SystersUser.objects.get(user=user)
        user2 = User.objects.create(username='foobar', password=self.password)
        systers_user2 = SystersUser.objects.get(user=user2)
        country = Country.objects.create(name='Bar', continent='AS')
        location = City.objects.create(name='Baz', display_name='Baz', country=country)
        meetup_location = MeetupLocation.objects.create(
            name="Foo", slug="foo", location=location,
            description="It's a test meetup location", leader=systers_user2)
        meetup_location.members.add(systers_user)
        members_group = Group.objects.get(name=COMMUNITY_MEMBER.format(meetup_location.name))
        self.assertEqual(user.groups.get(), members_group)

    def test_add_meetup_location_moderators(self):
        """Test addition of permissions to a user when she is made a meetup location moderator"""
        user = User.objects.create(username='foo', password=self.password)
        systers_user = SystersUser.objects.get(user=user)
        user2 = User.objects.create(username='foobar', password=self.password)
        systers_user2 = SystersUser.objects.get(user=user2)
        country = Country.objects.create(name='Bar', continent='AS')
        location = City.objects.create(name='Baz', display_name='Baz', country=country)
        meetup_location = MeetupLocation.objects.create(
            name="Foo", slug="foo", location=location,
            description="It's a test meetup location", leader=systers_user2)
        meetup_location.moderators.add(systers_user)
        moderators_group = Group.objects.get(name=COMMUNITY_MODERATOR.format(meetup_location.name))
        self.assertEqual(user.groups.get(), moderators_group)

    def test_delete_meetup_location_members(self):
        """Test removal of permissions from a user when she is removed as a meetup location
        member"""
        user2 = User.objects.create(username='foobar', password=self.password)
        systers_user2 = SystersUser.objects.get(user=user2)
        user = User.objects.create(username='foo', password=self.password)
        systers_user = SystersUser.objects.get(user=user)
        country = Country.objects.create(name='Bar', continent='AS')
        location = City.objects.create(name='Baz', display_name='Baz', country=country)
        meetup_location = MeetupLocation.objects.create(
            name="Foo", slug="foo", location=location,
            description="It's a test meetup location", leader=systers_user2)
        members_group = Group.objects.get(name=COMMUNITY_MEMBER.format(meetup_location.name))
        meetup_location.members.add(systers_user)
        self.assertEqual(user.groups.get(), members_group)
        meetup_location.members.remove(systers_user)
        self.assertEqual(len(user.groups.all()), 0)

    def test_delete_meetup_location_moderators(self):
        """Test removal of permissions from a user when she is removed as a meetup location
        moderator"""
        user2 = User.objects.create(username='foobar', password=self.password)
        systers_user2 = SystersUser.objects.get(user=user2)
        user = User.objects.create(username='foo', password=self.password)
        systers_user = SystersUser.objects.get(user=user)
        country = Country.objects.create(name='Bar', continent='AS')
        location = City.objects.create(name='Baz', display_name='Baz', country=country)
        meetup_location = MeetupLocation.objects.create(
            name="Foo", slug="foo", location=location,
            description="It's a test meetup location", leader=systers_user2)
        moderators_group = Group.objects.get(name=COMMUNITY_MODERATOR.format(meetup_location.name))
        meetup_location.moderators.add(systers_user)
        self.assertEqual(user.groups.get(), moderators_group)
        meetup_location.moderators.remove(systers_user)
        self.assertEqual(len(user.groups.all()), 0)

    def test_create_notice_types(self):
        """Test creation of notice types"""
        notice_types = NoticeType.objects.all()
        self.assertEqual(len(notice_types), 7)
        new_join_request = NoticeType.objects.get(label="new_join_request")
        self.assertEqual(new_join_request.display, "New Join Request")
        joined_meetup_location = NoticeType.objects.get(label="joined_meetup_location")
        self.assertEqual(joined_meetup_location.display, "Joined Meetup Location")
        made_moderator = NoticeType.objects.get(label="made_moderator")
        self.assertEqual(made_moderator.display, "Made moderator")
        new_meetup = NoticeType.objects.get(label="new_meetup")
        self.assertEqual(new_meetup.display, "New Meetup")
        new_support_request = NoticeType.objects.get(label="new_support_request")
        self.assertEqual(new_support_request.display, "New Support Request")
        support_request_approved = NoticeType.objects.get(label="support_request_approved")
        self.assertEqual(support_request_approved.display, "Support Request Approved")
        new_meetup_request = NoticeType.objects.get(label="new_meetup_request")
        self.assertEqual(new_meetup_request.display, "New Meetup Request")
