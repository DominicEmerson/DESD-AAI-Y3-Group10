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

Any problems contact me --- after tomorrow :D
