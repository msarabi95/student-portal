from clubs.models import Club
from clubs.utils import get_user_coordination_and_deputyships
from accounts.utils import get_user_gender
from bulb.models import MAXIMUM_GROUP_MEMBERS

def is_bulb_coordinator_or_deputy(user):
    coordination_and_deputyships = get_user_coordination_and_deputyships(user)
    return coordination_and_deputyships.filter(english_name='Bulb').exists()

def get_bulb_club_for_user(user):
    user_gender = get_user_gender(user)
    if user_gender == 'F':
        return Club.objects.current_year().get(english_name="Bulb",
                                               gender="F")
    else:
        return Club.objects.current_year().get(english_name="Bulb",
                                               gender="M")

def get_bulb_club_of_user(user):
    coordination_and_deputyships = get_user_coordination_and_deputyships(user)
    bulb = coordination_and_deputyships.filter(english_name='Bulb')
    if bulb.exists():
        return bulb.first()
    else:
        return None

def can_edit_book(user, book):
    if is_bulb_coordinator_or_deputy(user) or \
       user.is_superuser or \
       book.submitter == user:
        return True
    else:
        return False

def can_order_book(user, book):
    if book.is_deleted or \
       user == book.submitter or \
       not book.is_available:
        return False
    else:
        return True

def can_edit_group(user, group):
    if is_bulb_coordinator_or_deputy(user) or \
       user.is_superuser or \
       group.coordinator == user:
        return True
    else:
        return False

def group_can_have_sessions(group):
    if not group.is_deleted and \
       group.membership_set.filter(is_active=True).count() >= 3:
        return True
    else:
        return False

def can_join_group(user, group):
    if group.is_deleted or \
       group.membership_set.filter(user=user).exists() or \
       group.membership_set.active().count() > MAXIMUM_GROUP_MEMBERS or \
       group.coordinator == user or \
       (group.gender and get_user_gender(user) != group.gender) or \
       group.membership_set.filter(user=user).exists():
        return False
    else:
        return True

   #get_user_gender(group.coordinator) != group.coordinator(user) or \

def is_active_group_member(user, group):
    return group.membership_set.filter(user=user, is_active=True).exists()
    
def can_edit_reader_profile(user, reader_profile):
    if is_bulb_coordinator_or_deputy(user) or \
       user.is_superuser or \
       reader_profile.user == user:
        return True
    else:
        return False
