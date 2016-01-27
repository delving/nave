Development setup
=================

Nave has support for running multiple projects from one development environment. The key concept is the 'project name'.

However that is not recomended, please rather checkout each project in a separate environment if you use virtualenvwrapper, this way you can prepare env variables to reduce redundant work and typos leading you to deploy the wrong project...


Initial dependencies, os x (why run anything else??)
----------------------------------------------------
Assuming you have brew install already you can execute the following command

    brew upgrade
    
    brew install python postgresql postgis elasticsearch rabbitmq 



Seting up environ and checking out the project
----------------------------------------------
The recomended method is to use virtualenvwrapper https://github.com/delving/nave_private/blob/master/docs/dev_setup_virtualenvwrapper.rst

If you are using fish, here is some documentation https://github.com/delving/nave_private/blob/master/docs/dev_setup_fish.rst

Creating a new project
----------------------
In nave/projects you can create a copy of *default* and name that project name. This name is then used by convention for:

* databasename
* app name in projects
* name for virtual environment
* name for triple store database
* name for the elastic search database

For the *test/acceptance* setup the *project name* is also prepended to the test data-sources.

In the following sections your chosen *project name* needs to be inserted where you see *{project name}*


Managing Postgresql for a project
---------------------------------
{project name} would be something like norvegiana

Create the Postgresql database:
::

    createdb {project name}
    psql -d {project name} -c "CREATE EXTENSION postgis; CREATE EXTENSION postgis_topology;"

Create the postgresql user for this project, as defined in the DATABASES block in 
projects/{project name}/local_settings.py. On creation you will be asked for this user's password.
::

    createuser { user name } --pwprompt
    
If you need to start again to get a clean db you can run the following one-liner:
::

    dropdb {project name}; createdb {project name}; psql -d  {project name} -c "CREATE EXTENSION postgis; CREATE EXTENSION postgis_topology;"


If you want to use ipython or the debugtoolbar you need to also install the following.
::

    pip install -r ../requirements/local.txt ../requirements/ipython.txt



Daemons needing to run before startig nave
::

    postgresql
    elasticsearch (1.7 or 1.7.1)


In the nave dir, Create the django database, tehn run django
::

    mv wsgi.py.template wsgi.py
    python manage.py syncdb
    python manage.py migrate
    python manage.py runserver

Test if you are up and running, visit: http://localhost:8000/admin.
