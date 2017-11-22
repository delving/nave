============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given. 


Types of Contributions
----------------------

You can contribute in many ways:


Report Bugs
~~~~~~~~~~~

Report bugs at https://github.com/delving/nave/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* If you can, provide detailed steps to reproduce the bug.
* If you don't have steps to reproduce the bug, just note your observations in
  as much detail as you can. Questions to start a discussion about the issue
  are welcome.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug"
is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "please-help" is open to whoever wants to implement it.

Please do not combine multiple feature enhancements into a single pull request.

Note: this project is very conservative, so new features that aren't tagged
with "please-help" might not get into core. We're trying to keep the code base
small, extensible, and streamlined. Whenever possible, it's best to try and
implement feature ideas as separate projects outside of the core codebase.

Write Documentation
~~~~~~~~~~~~~~~~~~~

Nave could always use more documentation, whether as part of the
official Nave docs, in docstrings, or even on the web in blog posts,
articles, and such.

If you want to review your changes on the documentation locally, you can do::

    pip install -r docs/requirements.txt
    make servedocs

This will compile the documentation, open it in your browser and start
watching the files for changes, recompiling as you save.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at
https://github.com/delving/nave/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)



Setting Up the Code for Local Development
-----------------------------------------

Here's how to set up `Nave` for local development.

1. Fork the `nave` repo on GitHub.
2. Clone your fork locally::

    $ git clone git@github.com:your_name_here/nave.git

3. Install your local copy into a virtualenv. Assuming you have virtualenvwrapper installed, this is how you set up your fork for local development::

    $ mkvirtualenv nave 
    $ cd nave/

See 'docs/dev_setup.rst' for more detailed instructions.

4. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

Now you can make your changes locally.

5. When you're done making changes, check that your changes pass the tests and flake8::

    $ pip install tox
    $ tox

Please note that tox runs flake8 automatically, since we have a test environment for it.

If you feel like running only the flake8 environment, please use the following command::

    $ tox -e flake8

6. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

7. Check that the test coverage hasn't dropped::

    $ tox -e cov-report

8. Submit a pull request through the GitHub website.



Contributor Guidelines
----------------------

Pull Request Guidelines
~~~~~~~~~~~~~~~~~~~~~~~

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list in README.rst.
3. The pull request should work for Python 3.5, 3.6
   and Travis CI.
4. Check https://travis-ci.org/delving/nave/pull_requests to ensure the tests pass for all supported Python versions and platforms.

Coding Standards
~~~~~~~~~~~~~~~~

* PEP8
* Functions over classes except in tests
* Quotes via http://stackoverflow.com/a/56190/5549

  * Use double quotes around strings that are used for interpolation or that are natural language messages
  * Use single quotes for small symbol-like strings (but break the rules if the strings contain quotes)
  * Use triple double quotes for docstrings and raw string literals for regular expressions even if they aren't needed.
  * Example:

    .. code-block:: python

        LIGHT_MESSAGES = {
            'English': "There are %(number_of_lights)s lights.",
            'Pirate':  "Arr! Thar be %(number_of_lights)s lights."
        }

        def lights_message(language, number_of_lights):
            """Return a language-appropriate string reporting the light count."""
            return LIGHT_MESSAGES[language] % locals()

        def is_pirate(message):
            """Return True if the given message sounds piratical."""
            return re.search(r"(?i)(arr|avast|yohoho)!", message) is not None

  * Write new code in Python 3.



Testing with tox
----------------

Tox uses py.test under the hood, hence it supports the same syntax for selecting tests.

For further information please consult the `pytest usage docs`_.

To run a particular test class with tox::

    $ tox -e py '-k TestFindHooks'

To run some tests with names matching a string expression::

    $ tox -e py '-k generate'

Will run all tests matching "generate", test_generate_files for example.

To run just one method::

    $ tox -e py '-k "TestFindHooks and test_find_hook"'


To run all tests using various versions of python in virtualenvs defined in tox.ini, just run tox.::

    $ tox

This configuration file setup the pytest-cov plugin and it is an additional
dependency. It generate a coverage report after the tests.

It is possible to tests with some versions of python, to do this the command
is::

    $ tox -e py35,py36

Will run py.test with the python3.5, python3.6 interpreters, for
example.

If you support multiple versions of Django you should have targets for those too.

Troubleshooting for Contributors
--------------------------------



Core Committer Guide
====================

Process: Pull Requests
----------------------

If a pull request is untriaged:

* Look at the roadmap
* Set it for the milestone where it makes the most sense
* Add it to the roadmap

How to prioritize pull requests, from most to least important:

#. Fixes for broken tests. Broken means broken on any supported platform or Python version.
#. Extra tests to cover corner cases.
#. Minor edits to docs.
#. Bug fixes.
#. Major edits to docs.
#. Features.


Process: Issues
---------------

If an issue is a bug that needs an urgent fix, mark it for the next patch release.
Then either fix it or mark as please-help.

For other issues: encourage friendly discussion, moderate debate, offer your thoughts.

New features require a +1 from 2 other core committers (besides yourself).

Process: Roadmap
----------------

The roadmap is https://github.com/delving/nave/milestones?direction=desc&sort=due_date&state=open

Due dates are flexible. Core committers can change them as needed. Note that GitHub sort on them is buggy.

How to number milestones:

* Follow semantic versioning. See http://semver.org

Milestone size:

* If a milestone contains too much, move some to the next milestone.
* Err on the side of more frequent patch releases.

Process: Pull Request merging and HISTORY.rst maintenance
---------------------------------------------------------

If you merge a pull request, you're responsible for updating `AUTHORS.rst` and `HISTORY.rst`

When you're processing the first change after a release, create boilerplate following the existing pattern:

.. code-block:: rest

    x.y.z (Development)
    ~~~~~~~~~~~~~~~~~~~

    The goals of this release are TODO: release summary of features

    Features:

    * Feature description, thanks to @contributor (#PR).

    Bug Fixes:

    * Bug fix description, thanks to @contributor (#PR).

    Other changes:

    * Description of the change, thanks to @contributor (#PR). 
                      
    .. _`@contributor`: https://github.com/contributor

Process: Accepting Template Pull Requests
-----------------------------------------

#. Run the template to generate the project.
#. Attempt to start/use the rendered project.
#. Merge the template in.
#. Update the history file.

.. note:: Adding a template doesn't give authors credit.


Process: Your own code changes
------------------------------

All code changes, regardless of who does them, need to be reviewed and merged by someone else.
This rule applies to all the core committers.

Exceptions:

* Minor corrections and fixes to pull requests submitted by others.
* While making a formal release, the release manager can make necessary, appropriate changes.
* Small documentation changes that reinforce existing subject matter. Most commonly being, but not limited to spelling and grammar corrections.

Responsibilities
----------------

#. Ensure cross-platform compatibility for every change that's accepted. Mac, Debian & Ubuntu Linux.
#. Create issues for any major changes and enhancements that you wish to make. Discuss things transparently and get community feedback.
#. Don't add any classes to the codebase unless absolutely needed. Err on the side of using functions.
#. Keep feature versions as small as possible, preferably one new feature per version.
#. Be welcoming to newcomers and encourage diverse new contributors from all backgrounds. See the Python Community Code of Conduct (https://www.python.org/psf/codeofconduct/).

Becoming a Core Committer
-------------------------

Contributors may be given core commit privileges. Preference will be given to those with:

A. Past contributions to Nave and other open-source projects. Contributions to Nave include both code (both accepted and pending) and friendly participation in the issue tracker. Quantity and quality are considered.
B. A coding style that the other core committers find simple, minimal, and clean.
C. Access to resources for cross-platform development and testing.
D. Time to devote to the project regularly.

