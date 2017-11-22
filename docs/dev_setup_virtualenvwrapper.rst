Working with virtualenvwrapper
------------------------------
Setting up a virtual env for a nave project, general idea is to have one virtualenv per project/customer to keep environments more clearly separated, and also to be able to preset ENV variables specific for this project.

This doc only lists virtualenvwrapper specifics, for the general instructions about your dev environ see dev_setup.rst


Initial setup of virtualenvwrapper
----------------------------------

::

  pip install virtualenvwrapper # this is run from your main python so might be pip3 instead
  mkdir ~/Envs
  echo "export WORKON_HOME=~/Envs" >> ~/.bash_profile
  echo "source virtualenvwrapper.sh" >> ~/.bash_profile


Start new terminal to ensure this environ is set. If virtualenvwrapper.sh fails open it and follow the detailed instructions how to ensure it is using the intended python interpreter.

::

  echo 'cd $VIRTUAL_ENV' >> $WORKON_HOME/postactivate
  echo "cd ~" >> $WORKON_HOME/postdeactivate # optional, leaves project on deactivation


Setting up a virtualenv for a specific project
----------------------------------------------
Lets use demo as a sample, if working on another project replace demo below with your project name

::

  mkvirtualenv --python=/usr/local/bin/python3.5 nave_demo
  git clone git@github.com:delving/nave.git nave_app
  echo 'export DJANGO_SETTINGS_MODULE="nave.projects.demo.settings"' >> $VIRTUAL_ENV/bin/postactivate
  echo "cd nave_app" >> $VIRTUAL_ENV/bin/postactivate
  pip install -r nave_app/requirements/base.txt

Checking out the specific project files

::

  cd nave/nave/projects
  git clone git@github.com:delving/hub3_demo.git demo
  deactivate 

Working on a virtualenv then leaving it
---------------------------------------
::

  workon nave_demo
  git pull  # Could be added to $VIRTUAL_ENV/bin/postactivate for convenience
  ...
  deactivate
