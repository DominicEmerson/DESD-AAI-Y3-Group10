================================
MAJOR UPDATE: 28/04/2025
Bradley Booth
Complete reorg of project root
Separation of Docker components into distinct subfolders
Implementation of frontend container for web server proxy
Postgres DB now persistent in isolated Database container
Main Django project (name: insurance_ai) isolated into backend container
Backend refactored into distinct apps following MVT:
  Authentication - login, security etc
  Claims - Enduser/Claims handler functionality (create, edit, view claims)
  Engineer - ML Engineer functionality (upload + retrain models, #TODO model performance view? Add models to database)
  Finance - Finance functionality (reports, invoices)
  Sysadmin - Admin functionality (user administration, health status)

Although user related models have been moved to the authentication app, these database tables continue to use the original name 'claims'
Preserving the original table name is controlled with the following declaration:
    class Meta:
        db_table = 'claims_customuser'  

If you make changes to the models structure in any apps you may need to drop the database and repopulate with dummy script data again!

Frontend webport is now 8080 (#TODO - change to 443 using SSL)
Other containers no longer expose ports outside of the Docker network
If you need to test anything direct to other containers you will need to edit the docker-compose and dockerfile to re-enable the ports.

I've tested as much as possible, but there may be some issues, please check any functionality that you previously implemented!

=================================


Instructions to run and build in VSCode:

Have Docker installed and running

Have MySQl installed.

New version runs py 3.12 rather than 3.10

No longer need powershell commands to stop windows changing lf to clrf as .sh no longer required.

In VSCode terminal:

'cd DESD-AAI-Y3-Group10'

docker-compose up --build -d

Once complete and all three showing green in docker

---

Update 03/04/25 - Dom

Commands in terminal if you want to check Ahmed's container/API is working on your machine:

docker-compose exec mlaas python manage.py makemigrations ml_api

docker-compose exec mlaas python manage.py migrate

docker-compose exec mlaas ls

docker-compose exec mlaas python manage.py register_models

curl -Method POST `     -Uri "http://localhost:8009/api/algorithms/1/predict/"`
-ContentType "application/json" `
-Body '{"input_data": [[0.5, 1.2, 3000]], "algorithm_name": "3-Feature Regression Model"}'

---

Update 19/03/2025 - Dom

The docker-compose.yml and relevant files have been updated so that postgre now mounts a persistent database that should save changes (provided you don't completely rebuild the containers).
The first time you run docker-compose --build -d it should automatically make migrations now, and create a set of default users.

When exiting a session you should use docker-compose down.

When starting a new session docker-compose up.

In these cases database updates will be persistent.

Also fixed broken jira updater.

---

If you try some front end work you will need to restart the django app with: docker restart insurance_ai-django_app-1

If you do any back end table addition or the like you will need to rebuild : docker-compose up --build -d (if you do this any changes you made to the db will not persist as you have rebuilt it).

If you want to stop docker with all containers left as they are between uses: docker-compose stop

To resume from stop: docker-compose start

---

If gou fuck up realy bad and want to get rid of all docker containers and any atifacts:

docker-compose down -v --rmi all --remove-orphans

docker system prune -a --volumes

\*\*\*Further:

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

Check if a user exists.

docker exec -it desd-aai-y3-group10-django_app-1 python manage.py shell

from claims.models import CustomUser
print(CustomUser.objects.all())  # Should list all users
exit()
```
