Instructions to run and build in VSCode:

Have Docker installed and running

Have MySQl installed.

clone the right branch (currently test branch) ** git clone --branch Dom-Test0703 --single-branch https://github.com/DominicEmerson/DESD-AAI-Y3-Group10.git

If you're on windows in powershell run run git config --global core.autocrlf false

In VSCode terminal: 
cd DESD-AAI-Y3-Group10
docker-compose up -d

Once complete and all three showing green in docker

docker exec -it desd-aai-y3-group10-django_app-1 python manage.py migrate

docker-compose exec django_app python manage.py makemigrations

docker-compose exec django_app python manage.py migrate

Then load some initial data

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
