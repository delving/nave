# Projects README

The private project settings and code should be stored in a separated GIT repository. The name of this repository should be the site-id that should be consistently used everywhere. You can copy the 'vagrant' directory and replace 'vagrant' with your 'site-id'. Then include your private repository as a folder with the following command (make sure you don't commit the folder in the main repository):

	$ git clone git@mygithost:<git-repo> <site-id>

To start developing create and activating a virtual environment for the 'site-id' using python 3.4+, copy the 'local_settings.py.template to 'local_settings.py' and export the DJANGO_SETTINGS_MODULE

	$ export DJANGO_SETTINGS_MODULE="projects.<site-id>.settings"

Install the requirements:

	$ pip install -r ../requirements/base.txt

Run the migrations:

    $ python manage.py migrate

Now you can start the project from the nave directory (where your manage.py file is) with:

	$ python manage.py runserver

If you run into an `wsgi` related error make sure you have 'wsgi.py' file in the nave directory. You can copy it directly from the 'wsgi.py.template' file.


Aprox time 19mins