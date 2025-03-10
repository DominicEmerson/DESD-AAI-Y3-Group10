Instructions to run and build in VSCode:

Have Docker installed and running

Have MySQl installed.

New version runs py 3.12 rather than 3.10

No longer need powershell commands to stop windows changing lf to clrf as .sh no longer required.

clone the right branch (currently test branch) ** 

git clone --branch PostgreTest https://github.com/DominicEmerson/DESD-AAI-Y3-Group10.git

In VSCode terminal: 
cd DESD-AAI-Y3-Group10

docker-compose up -d

Once complete and all three showing green in docker

docker exec -it desd-aai-y3-group10-django_app-1 python manage.py makemigrations

docker exec -it desd-aai-y3-group10-django_app-1 python manage.py migrate


docker exec -it desd-aai-y3-group10-django_app-1 python manage.py showmigrations

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
