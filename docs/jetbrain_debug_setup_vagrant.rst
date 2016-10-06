Setting up Jetbrains IDE for vagrant debug mode (.e.g. Intellij Idea, PyCharm, etc.)
====================================================================================

This document details the steps necessary to configure an Jetbrains IDE for remote running/debugging of Django projects. It breaks down in the following steps:

* Setting up a remote vagrant-based Python SDK
* Creating the right django settings 
* Setting up the run-configuration

Remote vagrant-based Python SDK
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once the Jetbrains IDE is open perform the following steps:

* File > Project Structure
* Select 'SDKs' in the left column under 'Platform Settings' of the pop-up window
* Click the green + icon
* Select 'Python SDK'
* Select 'Add remote'
* Select the 'vagrant' radio-button
* In 'Vagrant Instance Folder' select the directory of your VagrantFile
* intellij will select the right host on port 2222
* In the 'Python interpreter path' select the full path to the virtualenv: `/opt/hub3/{orgId}/virtenv/bin/python3` 
* Click on the 'OK' button

Now intellij will add its extra dependencies which are needed for running and debugging to the classpath of virtualenv. This SDK is now ready to use.

Make sure you change the name of the SDK in the 'name' field of the overview. The default generated name is long and difficult to read since the import part is often hidden in the input field. When you later need to select your 'run configuration' SDK it will be difficult to find the right one if you don't change the name.


Configuring the Django settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When the Django settings are discovered by the Jetbrains IDE, you often still need to specify where the 'manage.py' file is located in your project. Without it you won't be able to run the Django application from within the IDE

* File > Project Structure
* Select 'Facets' in the left column under 'Project Settings' of the pop-up window.
* In the right pane select the 'Django' facet.
* In the 'Settings' field select the main settings file in the File Browser window. (Click on the ellipsis '...' next to the window.)
* In the 'Manage script' field select the 'manage.py' file in the File Browser window.
* Click on 'apply' and 'ok'


Setting up the Run-Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Run > Edit Configurations
* Click the green + icon
* Select 'Django Server'
* In the 'Configuration' tab set the following values:
    * 'Host' to '0.0.0.0'
    * 'Port' to '8000'
    * 'Environment variables' to 'DJANGO_SETTINGS_MODULE=projects.{orgId}.settings' 
    * 'use specified interpreter' to the SDK you created in step 1
    * 'Path mappings' to '{path on your computer to nave}=/opt/hub3/{orgId}/nave'. Note that this is to path to the dir that has the 'manage.py' file.
* Click on 'apply' and 'ok'

Give the run configuration a sensible name. Having the orgId in the name of the run configuration is a good convention. 

Running the Project 
^^^^^^^^^^^^^^^^^^^

Now you are ready to run the project. Select the run configuration in the drop-down and then click the 'run' or 'debug' button. 
