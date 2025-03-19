Instructions to Run and Build in VSCode
Prerequisites:
Docker installed and running
MySQL installed
Python 3.12 (previously used 3.10)
No longer need PowerShell commands to stop Windows from changing LF to CRLF, as .sh scripts are no longer required.
Running the Project
Start the Project:
sh
Copy
Edit
cd DESD-AAI-Y3-Group10
docker-compose up --build -d
Wait until all three services show as green in Docker.
Key Updates (19/03/2025 - Dom)
PostgreSQL now mounts a persistent database, meaning data will be saved unless the containers are completely rebuilt.
First-time setup: Running docker-compose up --build -d will now automatically:
Apply migrations
Create a set of default users
Fixed broken Jira updater.
Managing the Project
Stopping and Restarting:
Stop the containers (without losing data):
sh
Copy
Edit
docker-compose down
Start a new session:
sh
Copy
Edit
docker-compose up
Stop Docker but keep all containers intact:
sh
Copy
Edit
docker-compose stop
Resume from a stopped state:
sh
Copy
Edit
docker-compose start
Restarting Services:
Restart the Django app (for front-end changes):
sh
Copy
Edit
docker restart insurance_ai-django_app-1
Rebuild after backend table changes (WARNING: This wipes the database!):
sh
Copy
Edit
docker-compose up --build -d
Cleaning Up Docker (if things go really wrong):
Remove all containers and images:
sh
Copy
Edit
docker-compose down -v --rmi all --remove-orphans
Prune Docker system (removes all volumes and cached data):
sh
Copy
Edit
docker system prune -a --volumes
GitHub & Jira Integration
GitHub is now linked. If you reference a Jira issue in a commit, use:

sh
Copy
Edit
git commit -m "Fix bug in authentication SCRUM-456"
git push origin main
Tested: Retroactive updates and status changes from GitHub work.
User Persistence & Automated Setup
Users now persist across restarts – Any new users added via Django Admin, API, or shell will be saved in the PostgreSQL database.
User creation is automated – On a fresh setup, default test users will be created automatically.
Updated docker-compose.yml – The startup process now:
Runs migrations
Ensures users exist before launching the app.
Checking Users in the Database:
sh
Copy
Edit
docker exec -it desd-aai-y3-group10-django_app-1 python manage.py shell
Then run:

python
Copy
Edit
from claims.models import CustomUser
print(CustomUser.objects.all())  # Should list all users
exit()



