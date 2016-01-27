Deploy to Server
================

Deploy a host with ubuntu 14.04 x64 (or similar)
================================================

Prepare the host with Ansible
-----------------------------


::

    Checkout git@github.com:delving/ansible.git


Create a file something like this, you can look at (nave_jhm.yml):

::

    ---
    #
    # this file can be run on a freshly deployed vm, will 1st do security updates etc
    # Next it will create the nave user and set up needed environments
    #
    - include: nave_fab_prepare.yml
      vars:
        hosts: "acc.jhm.delving.org,prod.jhm.delving.eu"
        nave_username: jhm
        nave_user_pw: "XXXX" #must match nave settings.py:FABRIC[SSH_PASS]

Add the used hostnames to a ansible hosts file, pointed to by -i

Run it something like this:
ansible-playbook -i other_files/production this_file.yml



Deploy Acceptance
-----------------
Run deploy in a python 2.7 environ...
::

    fab install
    fab create  # settings.py:FABRIC[SSH_PASS] needs to be given 3 times
    fab deploy # fails with error that can be ignored
    fab reload_supervisor
    fab restart
    fab deploy_narthex


Deploy Production
-----------------
::

    fab prod install
    fab prod create  # settings.py:FABRIC[SSH_PASS] needs to be given 3 times
    fab prod deploy # fails with error that can be ignored
    fab prod reload_supervisor
    fab prod restart
    fab prod deploy_narthex

Clean up steps
--------------
modify /etc/nginx/nginx.conf

::

    replace:
        include /etc/nginx/sites-enabled/*;
    with:
        include /etc/nginx/sites-enabled/*.conf;
  
then restart nginx
::

    http://HOSTNAME/admin
    login with: admin - ADMIN_PASS
    Under Authtoken, creat a token for user admin
    copy this token to ACC_NAVE_AUTH_TOKEN or PROD_NAVE_AUTH_TOKEN depending on deploy type
    then do
    fab [prod] deploy
    fab [prod] deploy_narthex


Creating the Narthex admin user
Go to http://data.culturebroker.se/narthex/
login with admin and a random suitable password of your choice (1st user creates his own password)
Save the user data.

After these steps the whole stack should be up and running.
