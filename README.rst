=========================================
 Chromium utils - command-line utilities 
=========================================

|build-status| |coverage-status|

:Version: 0.1.0
:Source: https://github.com/sgh7/chrome_utils/
:Keywords: command line, Linux, Google Chromium, python

--

Linux command-line utilities for Google's Chromium browser
==========================================================

Recently, I switched to Google Chromium and opened up a 
gazillion tabs.  If my previous browser, Firefox, got into
a memory resource exhaustion scenario, the Linux Out-Of-Memory
killer would claim it and I could recover most of what I had
been doing by restarting Firefox.  Because the Chromium
browser spawns many processes, I wanted to experiment to see
if I could selectively throttle the renderer processes that
were taking the most resources according to the ``top``
command.  Also, I wanted to be able to recover the timeline
of URL visits from the browser history.

- **chrome_throttle.py**

  - Allows the user (desktop Linux only) to query the list of
    process IDs that correspond to renderers, along with their
    Linux status codes.

  - Allow the user to selectively pause and un-pause a subset
    of the renderer process IDs.

- **chrome_history.py**

Allows the user the ability to recover the URL visit history.
The browser must either not be running, or a copy of the
*~/.config/chromium/Default/History* file must be made and
the program run against it.


Status
======

This software is experimental.


Installation
============

At the current time, there is no installation method other than
retrieving from github.


Bug tracker
===========

If you have any suggestions, bug reports or annoyances please report them
to the issue tracker at http://github.com/sgh7/chrome_utils/issues/


Wiki
====

http://wiki.github.com/sgh7/chrome_utils/


.. _maintainers:

Maintainers
===========

- `@sgh7`_ (primary maintainer)

.. _`@sgh7`: http://github.com/sgh7


.. _contributing-short:

Contributing
============

Development of `chrome_utils` happens at Github: http://github.com/sgh7/chrome_utils

.. _license:

License
=======

This software is licensed under the `New BSD License`. See the ``LICENSE``
file in the top distribution directory for the full license text.

.. # vim: syntax=rst expandtab tabstop=4 shiftwidth=4 shiftround


.. |build-status| image:: https://travis-ci.org/sgh7/chrome_utils.svg?branch=master
   :target: https://travis-ci.org/sgh7/chrome_utils
.. |coverage-status| image:: https://coveralls.io/repos/sgh7/chrome_utils/badge.svg
   :target: https://coveralls.io/r/sgh7/chrome_utils
