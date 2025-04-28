# claims/management/commands/list_users.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Lists all existing users"

    def handle(self, *args, **kwargs):
        User = get_user_model()
        users = User.objects.all()

        if not users:
            self.stdout.write("No users found.")
        else:
            self.stdout.write("Existing users:\n")
            for user in users:
                self.stdout.write(f" - {user.username}, {user.email}, Role: {user.role}")
