Vagrant local development setup
===============================

Basic setup
^^^^^^^^^^^

    * clone the nave project:

        $ git clone git@github.com:delving/nave.git nave_public

    * go into the projects directory

        $ cd nave_public/nave/projects

    * clone your project

        $ git clone git@github.com:delving/hub3_{{ project }}.git {{ project }}

    * go into the project

        $ cd {{ project }}

    * create your local settings file

        $ cp local_settings.py.template local_settings.py

    * install plugins

        $ vagrant plugin install vagrant-hostsupdater
        $ vagrant plugin install vagrant-triggers

    * provision and start-up vagrant

        $ vagrant up

    * wait for ca 20 minutes for everthing to be installed and configured. When it is done stop and start vagrant

        $ vagrant halt
        $ vagrant up

    * now you can either login via `vagrant ssh` or you can go see the project in action on: http://{{project}}.localhost/


Full setup
==========

Install vagrant and virtual box on your development machine, see https://www.vagrantup.com for instructions
and the installer.

Install the hostupdate plugin

    $ vagrant plugin install vagrant-hostsupdater
    $ vagrant plugin install vagrant-triggers


Set the DJANGO_SETTINGS_MODULE variable, replace {{ PROJECT }} with your project name.
The default project is **vagrant**, if you run on a specific project copy nave/projects/vagrant and use that instead.
Note that the install scripts sets this setting by default in the ~/.profile setting

    $ export DJANGO_SETTINGS_MODULE="projects.{{ PROJECT }}.settings"

If you haven't setup your local dev environment you have to make a copy of 'nave/wsgi.py.template' and
'nave/projects/{{ PROJECT }}/local_settings.py.template'
Do NOT add those files to the repo!!

Then create the virtual machine. This will run all the provisioning steps as well. So get some coffee because
the first setup takes ca 15 minutes.

    $ vagrant up

And login to the machine in a separate terminal to verify vagant environ

    $ vagrant halt
    $ vagrant up
    $ vagrant ssh

You can check the following urls for a quick system check:

        * home page: http://{{ project }}.localhost/
        * search page: http://{{ project }}.localhost/search/
        * api search: http://{{ project }}.localhost/api/search/v1
        * sparql: http://{{ project }}.localhost/snorql
        * nathex: http://{{ project }}.localhost/narthex/
        * elasticsearch: http://{{ project }}.localhost:9200
        * flower celery monitor: http://{{ project }}.localhost:5555
        * fuseki triple-store: http://{{ project }}.localhost:3030


Dev Setup
^^^^^^^^^

To get the 'live reload' version of Django run the following steps on the guest machine, i.e. after you have run
`vagrant ssh`.


    $ cd {{ project }}/project/nave
    $ workon {{ project }}
    $ python manage.py runserver 0.0.0.0:8000

Now you can navigate to "http://{{ project }}.localhost:8000" for the development version. All changes  you
make in your preferred IDE are now picked up and reloaded on the guest machine.

When you have made changes to the configuration files of the services or to files related to the celery tasks
that interact with the Queue manager you have to rerun the following command:

    $ workon {{ project }}_2
    $ fab local deploy_dev
    $ workon {{ project }}


vagrant good-to-knows
^^^^^^^^^^^^^^^^^^^^^

Access
    $ vagrant ssh

Re-provision

    $ vagrant provision

Starting the vagrant

    $ vagrant up

Stopping it

    $ vagrant halt

Erasing the environ

    $ vagrant destroy


Vagrant Jetbrains IDE (PyCharm/Intellij Idea) debug Setup
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. todo add documentation how to setup the development environment. 

* Set up vagrant 
* setup remote python
* Configure the run configuration
