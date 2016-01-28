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
Lets use culturebroker as a sample, if working on another project replace culturebroker below with your project name

::

  mkvirtualenv --python=/usr/local/bin/python3.5 nave_norvegiana
  git clone git@github.com:delving/nave.git
  echo 'export DJANGO_SETTINGS_MODULE="projects.norvegiana.settings"' >> $VIRTUAL_ENV/bin/postactivate
  echo "cd nave/nave" >> $VIRTUAL_ENV/bin/postactivate
  pip install -r nave/requirements/base.txt

The wheel builds are failing ATM (2015-12-03) this is a minor issue, if you rerun the pip install with no errors your fine.

Delete all but the current project (if commited), default and __init__.py from this environ, not strictly needed, but makes codebase cleaner and reduces risk of ending up working on an unintended project


  

::

  mkdir /tmp/new_nave
  cd nave_private/nave/projects
  mv __init__.py /tmp/new_nave
  mv default /tmp/new_nave
  # mv culturebroker /tmp/new_nave # only run this if your project is already committed
  rm -rf ../projects/*    # minimize risk of deleteing something unintended
  mv /tmp/new_nave/* .
  rmdir /tmp/new_nave
  # rsync -avP default/ culturebroker; cd culturebroker # Only run if you are creating a new project
  # cd culturebroker # only run this if your project is already committed
  cp local_settings.py.template local_settings.py
  deactivate


Working on a virtualenv then leaving it
---------------------------------------
::

  workon nave_culturebroker
  git pull  # Could be added to $VIRTUAL_ENV/bin/postactivate for convenience
  ...
  deactivate
