# Projects README

The private project settings and code should be stored in a separated GIT repository. The name of this repository should be the site-id that should be consistently used everywhere. You can copy the 'vagrant' directory and replace 'vagrant' with your 'site-id'. Then include your private repository as a folder with the following command (make sure you don't commit the folder in the main repository):

	$ git clone git@mygithost:<git-repo> <site-id>

At this point, you can import the project into your IDE. If you are an IntelliJ user, you probably want to add both the
nave directory and your project directory as 'version control' root folders.

After that, `cd` into your project directory.

Then, prepare the Django local settings by copying the template file inside the project-directory, and modifying it.

```bash
cp local_settings.py.template local_settings.py
```

For development purposes, set the Debug flag inside your newly created local_settings.py to True (or all kinds of paths will yield 404s)

After that, fire up your vagrant box:

`vagrant up`

This will install all the required hub3-software and it will link in the nave-directory on your workstation through a
Vagrant share.

If you like, you can add the following aliases to the `.profile` file on the vagrant-box:

```bash
alias sctl="sudo supervisorctl"
alias pmp="python manage.py"
alias pmp2="python ../../manage.py"
alias kill_guni="sudo supervisorctl stop jck:gunicorn"
alias nave="cd jck/project/nave"
alias go="workon jck && sctl stop jck:gunicorn && cd jck/project/nave && python manage.py runserver 0.0.0.0:8000"
alias rundev="pmp runserver 0.0.0.0:8000"
```