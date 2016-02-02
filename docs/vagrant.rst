Vagrant local development setup
===============================

Basic setup
^^^^^^^^^^^

Install vagrant and virtual box on your development machine

Install the hostupdate plugin

    $ vagrant plugin install vagrant-hostsupdater


Set the DJANGO_SETTINGS_MODULE variable (replace 'vagrant' with your project name in the projects folder if you run on a specific project)

    $ export DJANGO_SETTINGS_MODULE="projects.vagrant.settings"

Then create the virtual machine

    $ vagrant up

Provision the machine

    $ vagrant provision

And login to the machine

    $ vagrant ssh


Basic deploy
^^^^^^^^^^^^

install virtual env

    $ mkvirtualenv -p python2 vagrant_deploy

Activate virtualenv

    $ workon vagrant_deploy

Make sure the DJANGO_SETTINGS_MODULE is correct

Install the application

    $ fab install

Create the deployment environment

    $ fab create

Deploy the environment

    $ fab deploy

Deploy narthex

    $ fab deploy_narthex


You should now see the application on

    * http://vagrant.localhost/narthex
    * http://vagrant.localhost/api/search
    * http://vagrant.localhost/admin

You can find the login information for this development environment in the FABRIC section of 'projects/vagrant/setttings.py'


Setting up dev environment
^^^^^^^^^^^^^^^^^^^^^^^^^^


    $ vagrant ssh
    $ cd src
    $ export DJANGO_SETTINGS_MODULE="projects.vagrant.settings"
    $ source /usr/local/bin/virtualenvwrapper.sh
    $ mkvirtualenv -p /usr/bin/python3 vagrant
    $ workon vagrant
    $ cd nave
    $ python manage.py 0.0.0.0:8000

Now go to "http://vagrant.localhost:8000/api/search" and you can see your dev environment up and running


