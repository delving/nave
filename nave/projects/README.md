# Projects README

The private project settings and code should be stored in a separated GIT repository. The name of this repository should be the site-id that should be consistently used everywhere. You can copy the default directory and replace default with your 'site-id'. Then include you private repository as a git sub-module with the following command:

	$ git submodule add git@mygithost:<git-repo> <site-id>

To start developing create and activating a virtual environment for the 'site-id' using python 3.4+, copy the 'local_settings.py.template to 'local_settings.py' and export the DJANGO_SETTINGS_MODULE

	$ export DJANGO_SETTINGS_MODULE="projects.<site-id>.settings"

Install the requirements:

	$ pip install -r ../requirements/base.txt

Now you can start the project from the nave directory (where your manage.py file is) with:

	$ python manage.py runserver
