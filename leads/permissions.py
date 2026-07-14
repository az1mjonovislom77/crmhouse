from user.models import User


def can_assign_leads(user):
    return user.role in (User.UserRoles.ADMIN, User.UserRoles.SUPERADMIN)
