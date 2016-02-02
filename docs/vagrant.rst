Vagrant local development setup
===============================

Install vagrant and virtual box on your development machine

Install the hostupdate plugin

    $ vagrant plugin install vagrant-hostsupdater

install the 'fabric' plugin

    $ vagrant plugin install vagrant-fabric-provisioner

Set the DJANGO_SETTINGS_MODULE variable (replace 'vagrant' with your project name in the projects folder)

    $ export DJANGO_SETTINGS_MODULE="projects.vagrant.settings"

Then create the virtual machine

    $ vagrant up

Provision the machine

    $ vagrant provision

And login to the machine

    $ vagrant ssh

