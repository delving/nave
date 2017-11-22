Setting up the development environment for Nave
===============================================


Setting up the brew dependencies
--------------------------------

Assuming you have brew install already you can execute the following command

    brew upgrade
    
    brew install python postgresql postgis elasticsearch rabbitmq virtualenvwrapper


Setting up the virtual environments for each project
----------------------------------------------------


Steps to setup a virtualenv for a project. A project contains its own theme and sub-apps.
You must run the command from the same directory where your manage.py is.


    mkvirtualenv -r ../requirements/base.txt -a . --python=/usr/local/bin/python3 {name of the project}


This will install the virtual_env, install the requirements, and route to the current dir when you execute `workon`

The next step is to set the environment settings in ~/.virtualenvs/{name of the project}/bin/postactivate. Open the
file in an editor of your choice and add

    export DJANGO_SETTINGS_MODULE="nave.projects.{name of the project}.settings"


Next to the settings file in your project folder you have a local_settings.py.template. Copy this to *local_settings.py*
and fill in the defaults for this project.

Now you can execute the `workon {name of the project}`  and create the database with `createdb and syncdb`.


If you are working with a GIS db you need to execute the following commands:

    psql {your db name}
    create database {your db name};
    \c {your db name}
    CREATE EXTENSION postgis;
    CREATE EXTENSION postgis_topology;
    select postgis_lib_version();

The last command should not give any errors and give back the version of postgis you are using.


You should repeat these steps for each project you want to develop on.




