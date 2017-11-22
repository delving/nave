Development setup
=================

Nave has support for running multiple projects from one development environment. The key concept is the 'project name'.

However that is not recomended, please rather checkout each project in a separate environment if you use virtualenvwrapper, this way you can prepare env variables to reduce redundant work and typos leading you to deploy the wrong project...

This project will most likely work with python2.7, but we will only support python 3.5 or higher. 

Development requirements
------------------------

If you intend to develop on this project we expect basic proficiency with the following programming languages, frameworks and paradigms:

    * Python 3
    * Django 1.10 or higher
    * Django Rest Framework
    * Test Driven Development
    * PyTest testing framework
    * RDF and SPARQL
    * Linked Open Data Principles
    * Europeana Data Model (EDM)
    * Javascript (jquery), CSS (LeSS)
    * SQL database (Postgresql 9.3 or higher)
    * Elasticsearch 5
    * Apache Fuseki TripleStore 2.4.1 or higher
    * Git and git-flow

This project is developed on MacOS X and Linux. Your milage with Microsoft Windows may vary. We don't explicitely support it as a development platform.

Nave is currently in production on Ubuntu 14.04 (or higher) and RedHat based Linux distributions.

Initial dependencies
--------------------
Install the following dependencies:

    * python3
    * postgresql 9.3 or higher with postgis 2.3 or higher
    * elasticsearch 5 
    * rabbitmq

For MacOS X and assuming you have brew install already you can execute the following command

    brew upgrade
    
    brew install python postgresql postgis elasticsearch rabbitmq 

For other operating systems follow the guidelines of your preferred package manager.

Seting up environ and checking out the project
----------------------------------------------
The recomended method is to use virtualenvwrapper https://github.com/delving/nave_private/blob/master/docs/dev_setup_virtualenvwrapper.rst

If you are using fish, here is some documentation https://github.com/delving/nave_private/blob/master/docs/dev_setup_fish.rst


Creating a new project
----------------------
In nave_app/nave/projects you can create a copy of *demo* project (see http://github.com:delving/hub3_demo.git ) and name that project name. This name is then used by convention for:

* databasename
* app name in projects
* name for virtual environment
* name for triple store database
* name for the elastic search database

In the following sections your chosen *project name* needs to be inserted where you see *{project name}*


Managing Postgresql for a project
---------------------------------
{project name} would be something like norvegiana

Create the Postgresql database:
::

    createdb {project name}
    psql -d {project name} -c "CREATE EXTENSION postgis; CREATE EXTENSION postgis_topology;"

Create the postgresql user for this project, as defined in the DATABASES block in nave/projects/{project name}/local_settings.py. On creation you will be asked for this user's password.
::

    createuser { user name } --pwprompt
    
If you need to start again to get a clean db you can run the following one-liner:
::

    dropdb {project name}; createdb {project name}; psql -d  {project name} -c "CREATE EXTENSION postgis; CREATE EXTENSION postgis_topology;"

Installing the Apache fuseki database definition
------------------------------------------------

Create a Apache database definition inside {apache installation dir}/run/configuration. Take the demo.ttl example for the docs directory and change the variable 'demo' to the {project_name}

Restart apache and go to 'http://localhost:3030/{project_name}' to see if everything is working as expected.

Install dependencies
--------------------

If you want to use ipython or the debugtoolbar you need to also install the following.
::

    pip install -r ../requirements/local.txt ../requirements/ipython.txt


Running everything for the first time
-------------------------------------

Daemons needing to run before starting nave
::

    * postgresql (9.4 or higher)
    * elasticsearch (5.2 or higher)
    * Apache Fuseki (2.4.1 or higher)


In the nave dir, Create the django database, then run django
::

    mv wsgi.py.template wsgi.py
    EXPORT DJANGO_SETTINGS_MODULE="nave.projects.{project name}.settings"
    python manage.py migrate
    python manage.py runserver

Test if you are up and running, visit: http://localhost:8000/.

Loading data for the first time. You can load processed EDM data from Narthex with the following command
::

    python manage.py load_processed_name {spec} path/to/procesed_edm.xml

After running this you can see the search results at http://localhost:8000/search


Django Settings
---------------

There are three important places where the application is configured. These files are documented. You should at least have familiarized yourself with it:

    * nave/base_settings.py
    * nave/projects/{project name}/settings.py
    * nave/projects/{project name}/local_settings.py

They are loaded in this order. Which means that settigs from the local_settings will override settings from the base_settings. 


Contributing and code-guidelines
--------------------------------

For contributing guidelines consult the CONTRIBUTING.md file in the root of the repository. For code-guidelines, see CONTRIBUTING.rst.




