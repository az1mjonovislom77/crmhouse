from user.models import User


def is_lead_admin(user):
    return user.is_staff or user.role in (User.UserRoles.ADMIN, User.UserRoles.SUPERADMIN)


def can_assign_leads(user):
    return user.role in (User.UserRoles.ADMIN, User.UserRoles.SUPERADMIN)
