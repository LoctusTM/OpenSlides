from typing import Dict, List, Optional, Union, cast

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model

from .cache import element_cache
from .collection import CollectionElement


GROUP_DEFAULT_PK = 1  # This is the hard coded pk for the default group.
GROUP_ADMIN_PK = 2  # This is the hard coded pk for the admin group.


def get_group_model() -> Model:
    """
    Return the Group model that is active in this project.
    """
    try:
        return apps.get_model(settings.AUTH_GROUP_MODEL, require_ready=False)
    except ValueError:
        raise ImproperlyConfigured("AUTH_GROUP_MODEL must be of the form 'app_label.model_name'")
    except LookupError:
        raise ImproperlyConfigured(
            "AUTH_GROUP_MODEL refers to model '%s' that has not been installed" % settings.AUTH_GROUP_MODEL
        )


def has_perm(user: Optional[CollectionElement], perm: str) -> bool:
    """
    Checks that user has a specific permission.

    User can be a CollectionElement of a user or None.
    """
    group_collection_string = 'users/group'  # This is the hard coded collection string for openslides.users.models.Group

    # Convert user to right type
    # TODO: Remove this and make use, that user has always the right type
    user = user_to_collection_user(user)
    if user is None and not anonymous_is_enabled():
        has_perm = False
    elif user is None:
        # Use the permissions from the default group.
        default_group = CollectionElement.from_values(group_collection_string, GROUP_DEFAULT_PK)
        has_perm = perm in default_group.get_full_data()['permissions']
    elif GROUP_ADMIN_PK in user.get_full_data()['groups_id']:
        # User in admin group (pk 2) grants all permissions.
        has_perm = True
    else:
        # Get all groups of the user and then see, if one group has the required
        # permission. If the user has no groups, then use the default group.
        group_ids = user.get_full_data()['groups_id'] or [GROUP_DEFAULT_PK]
        for group_id in group_ids:
            group = CollectionElement.from_values(group_collection_string, group_id)
            if perm in group.get_full_data()['permissions']:
                has_perm = True
                break
        else:
            has_perm = False
    return has_perm


def in_some_groups(user: Optional[CollectionElement], groups: List[int]) -> bool:
    """
    Checks that user is in at least one given group. Groups can be given as a list
    of ids or group instances. If the user is in the admin group (pk = 2) the result
    is always true.

    User can be a CollectionElement of a user or None.
    """

    if len(groups) == 0:
        return False  # early end here, if no groups are given.

    # Convert user to right type
    # TODO: Remove this and make use, that user has always the right type
    user = user_to_collection_user(user)
    if user is None and not anonymous_is_enabled():
        in_some_groups = False
    elif user is None:
        # Use the permissions from the default group.
        in_some_groups = GROUP_DEFAULT_PK in groups
    elif GROUP_ADMIN_PK in user.get_full_data()['groups_id']:
        # User in admin group (pk 2) grants all permissions.
        in_some_groups = True
    else:
        # Get all groups of the user and then see, if one group has the required
        # permission. If the user has no groups, then use the default group.
        group_ids = user.get_full_data()['groups_id'] or [GROUP_DEFAULT_PK]
        for group_id in group_ids:
            if group_id in groups:
                in_some_groups = True
                break
        else:
            in_some_groups = False
    return in_some_groups


def anonymous_is_enabled() -> bool:
    """
    Returns True if the anonymous user is enabled in the settings.
    """
    from ..core.config import config
    return config['general_system_enable_anonymous']


async def async_anonymous_is_enabled() -> bool:
    """
    Like anonymous_is_enabled but async.
    """
    from ..core.config import config
    if config.key_to_id is None:
        await config.build_key_to_id()
        config.key_to_id = cast(Dict[str, int], config.key_to_id)
    element = await element_cache.get_element_full_data(config.get_collection_string(), config.key_to_id['general_system_enable_anonymous'])
    return False if element is None else element['value']


AnyUser = Union[Model, CollectionElement, int, AnonymousUser, None]


def user_to_collection_user(user: AnyUser) -> Optional[CollectionElement]:
    """
    Takes an object, that represents a user and converts it to a CollectionElement
    or to None, if it is an anonymous user.

    User can be
    * an user object,
    * a CollectionElement of an user,
    * an user id or
    * an anonymous user.

    Raises an TypeError, if the given user object can not be converted.
    """
    User = get_user_model()

    if user is None:
        # Nothing to do
        pass
    elif isinstance(user, CollectionElement) and user.collection_string == User.get_collection_string():
        # Nothing to do
        pass
    elif isinstance(user, CollectionElement):
        raise TypeError(
            "Unsupported type for user. Only CollectionElements for users can be"
            "used. Not {}".format(user.collection_string))
    elif isinstance(user, int):
        # user 0 means anonymous
        if user == 0:
            user = None
        else:
            user = CollectionElement.from_values(User.get_collection_string(), user)
    elif isinstance(user, AnonymousUser):
        user = None
    elif isinstance(user, User):
        # Converts a user object to a collection element.
        # from_instance can not be used because the user serializer loads
        # the group from the db. So each call to from_instance(user) costs
        # one db query.
        user = CollectionElement.from_values(User.get_collection_string(), user.id)
    else:
        raise TypeError(
            "Unsupported type for user. User {} has type {}.".format(user, type(user)))
    return user
