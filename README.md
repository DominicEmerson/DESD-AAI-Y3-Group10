Instructions to run and build in VSCode:

Have Docker installed and running

Have MySQl installed.

New version runs py 3.12 rather than 3.10

No longer need powershell commands to stop windows changing lf to clrf as .sh no longer required.


In VSCode terminal: 

'cd DESD-AAI-Y3-Group10'

docker-compose up --build -d

Once complete and all three showing green in docker


docker exec -it desd-aai-y3-group10-django_app-1 python manage.py migrate


docker exec -it desd-aai-y3-group10-django_app-1 python manage.py showmigrations

Then load some initial data
docker exec -it desd-aai-y3-group10-django_app-1 python manage.py makemigrations

docker-compose exec django_app python manage.py create_test_users

docker-compose exec django_app python manage.py import_claims

For 4 defualt users and claims info filled out

***Additional: 


If you try some front end work you will need to restart the django app with: docker restart insurance_ai-django_app-1

If you do any back end table addition or the like you will need to rebuild : docker-compose up --build -d

If you want to stop docker with all containers left as they are between uses: docker-compose stop

To resume from stop: docker-compose start



If gou fuck up realy bad and want to get rid of all docker containers and any atifacts: 


docker-compose down -v --rmi all --remove-orphans

docker system prune -a --volumes

Any problems contact me --- after tomorrow :D

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
docker-compose up -d

