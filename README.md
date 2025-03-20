Instructions to run and build in VSCode:

Have Docker installed and running

Have MySQl installed.

New version runs py 3.12 rather than 3.10

No longer need powershell commands to stop windows changing lf to clrf as .sh no longer required.


In VSCode terminal: 

'cd DESD-AAI-Y3-Group10'

docker-compose up --build -d

Once complete and all three showing green in docker

****

Update 19/03/2025 - Dom

The docker-compose.yml and relevant files have been updated so that postgre now mounts a persistent database that should save changes (provided you don't completely rebuild the containers).
The first time you run docker-compose --build -d it should automatically make migrations now, and create a set of default users.

When exiting a session you should use docker-compose down.

When starting a new session docker-compose up. 

In these cases database updates will be persistent.

Also fixed broken jira updater.

*** ***


If you try some front end work you will need to restart the django app with: docker restart insurance_ai-django_app-1

If you do any back end table addition or the like you will need to rebuild : docker-compose up --build -d (if you do this any changes you made to the db will not persist as you have rebuilt it).

If you want to stop docker with all containers left as they are between uses: docker-compose stop

To resume from stop: docker-compose start

*** ***

If gou fuck up realy bad and want to get rid of all docker containers and any atifacts: 


docker-compose down -v --rmi all --remove-orphans

docker system prune -a --volumes

***Further:

GitHub is now linked. I'm going to see if I can link some old issues. But anytime you address a jira issue in your GitHub commit you should tag the issue like this

git commit -m "Fix bug in authentication SCRUM-456"
git push origin main

Tested retroactive updates and status change from git.

### User Persistence & Automated Setup

- **Users now persist across restarts** – Any new users added via Django Admin, API, or shell will be saved in the PostgreSQL database.
- **User creation is automated** – On a fresh setup, default test users will be created automatically.
- **Updated `docker-compose.yml`** – The startup process now runs migrations and ensures users exist before launching the app.

#### How to Start the Project:
```sh
docker-compose up --build -d

stop without losing data
docker-compose down

Check if a user exists

docker exec -it desd-aai-y3-group10-django_app-1 python manage.py shell

from claims.models import CustomUser
print(CustomUser.objects.all())  # Should list all users
exit()