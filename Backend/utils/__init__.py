# ------------------------
# Role-Based Pages
# ------------------------
def is_admin(user):
    return user.is_authenticated and user.role == 'admin'
def is_engineer(user):
    return user.is_authenticated and user.role == 'engineer'
def is_finance(user):
    return user.is_authenticated and user.role == 'finance'
def is_enduser(user):
    return user.is_authenticated and user.role == 'enduser'
