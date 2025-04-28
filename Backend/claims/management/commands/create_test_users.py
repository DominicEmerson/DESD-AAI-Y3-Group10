from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = "Creates default test users for each role along with a specific superuser (Dominic)."

    def handle(self, *args, **kwargs):
        # Data for default test users
        users_data = [
            {"username": "Dominic", "email": "dominic@example.com", "password": "2your3t3rnity", "role": "admin", "is_staff": True, "is_superuser": True},
            {"username": "admin_user", "email": "admin@example.com", "password": "adminpass", "role": "admin", "is_staff": True, "is_superuser": True},
            {"username": "engineer_user", "email": "engineer@example.com", "password": "engineerpass", "role": "engineer"},
            {"username": "finance_user", "email": "finance@example.com", "password": "financepass", "role": "finance"},
            {"username": "enduser", "email": "enduser@example.com", "password": "enduserpass", "role": "enduser"},
        ]

        # Create the users if they don't already exist
        for user_data in users_data:
            if not User.objects.filter(username=user_data["username"]).exists():
                user = User.objects.create_user(
                    username=user_data["username"],
                    email=user_data["email"],
                    password=user_data["password"],
                    role=user_data["role"]
                )
                if user_data.get("is_staff"):
                    user.is_staff = True
                if user_data.get("is_superuser"):
                    user.is_superuser = True
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Created user: {user.username}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"User {user_data['username']} already exists."))

        self.stdout.write(self.style.SUCCESS("Default test users and specific superuser created!"))

