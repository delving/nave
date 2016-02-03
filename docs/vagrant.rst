Vagrant local development setup
===============================

Basic setup
^^^^^^^^^^^

Install vagrant and virtual box on your development machine, see https://www.vagrantup.com for instructions
and the installer.

Install the hostupdate plugin

    $ vagrant plugin install vagrant-hostsupdater


Set the DJANGO_SETTINGS_MODULE variable, replace {{ PROJECT }} with your project name.
The default project is **vagrant**, if you run on a specific project copy nave/projects/vagrant and use that instead.

    $ export DJANGO_SETTINGS_MODULE="projects.{{ PROJECT }}.settings"

If you haven't setup your local dev environment you have to make a copy of 'nave/wsgi.py.template' and
'nave/projects/{{ PROJECT }}/local_settings.py.template'
Do NOT add those files to the repo!!

Then create the virtual machine

    $ vagrant up

Provision the machine

    $ vagrant provision

And login to the machine in a separate terminal to verify vagant environ

    $ vagrant ssh

If you run a specific project you also have to create the user with the password that is
specified in the FABRIC section of your 'settings.py'. While ssh-ed into the guest machine

    $ sudo useradd {{ PROJECT }}
    $ sudo usermod -G sudo {{ PROJECT }}


Basic deploy
^^^^^^^^^^^^



Make sure you have sourced the virtualenvwrapper script

    $ source /usr/local/bin/virtualenvwrapper.sh

install virtual env for deployment.

    $ mkvirtualenv -p python2 vagrant_deploy

Activate virtualenv

    $ workon vagrant_deploy

Make sure you are located in the nave reop top dir and that DJANGO_SETTINGS_MODULE is correct

    $ pip install -r requirements/base.txt
    $ pip install fabric

    $ cd nave

Install the application

    $ fab install

Create the deployment environment

    $ fab create

Deploy the environment

    $ fab deploy

Deploy narthex

    $ fab deploy_narthex


You should now see the application on

    * http://{{ PROJECT }}.localhost/narthex
    * http://{{ PROJECT }}.localhost/api/search
    * http://{{ PROJECT }}.localhost/admin

You can find the login information for this development environment in the FABRIC section of 'projects/vagrant/setttings.py'


Setting up dev environment
^^^^^^^^^^^^^^^^^^^^^^^^^^


    $ vagrant ssh

    $ cd src

    $ export DJANGO_SETTINGS_MODULE="projects.{{ PROJECT }}.settings"

    $ source /usr/local/bin/virtualenvwrapper.sh

    $ mkvirtualenv -p /usr/bin/python3 {{ PROJECT }}

    $ workon {{ PROJECT }}

    $ cd nave

    $ python manage.py 0.0.0.0:8000

Now go to "http://{{ PROJECT }}.localhost:8000/api/search" and you can see your dev environment up and running


vagrant good-to-knows
^^^^^^^^^^^^^^^^^^^^^

Access

    $ vagrant ssh

Starting the vagrant

    $ vagrant up

Stopping it

    $ vagrant halt

Erasing the environ

    $ vagrant destroy