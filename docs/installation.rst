Installation and Configuration
==============================

.. code-block:: bash

  $ pip install django-staticfilesplus

In ``settings.py`` replace the default ``STATICFILES_FINDERS`` definition with this:

.. code-block:: python

  STATICFILES_FINDERS = (
      'staticfilesplus.finders.FileSystemFinder',
      'staticfilesplus.finders.AppDirectoriesFinder',
  )

And enable the default processors:

.. code-block:: python

  STATICFILESPLUS_PROCESSORS = (
      'staticfilesplus.processors.less.LESSProcessor',
      'staticfilesplus.processors.js.JavaScriptProcessor',
  )

Assuming that ``django.contrib.staticfiles`` is in your ``INSTALLED_APPS`` (which it is by
default) you're ready to go.


Settings
--------

.. attribute:: STATICFILESPLUS_PROCESSORS

    :default: ``()``

    A list of active processors. See the processor documentation for details on how
    these work.


.. attribute:: STATICFILESPLUS_TMP_DIR

    :default: ``os.path.join(STATIC_ROOT, 'staticfilesplus_tmp)``

    A directory in which to write temporary working files. If it doesn't exist it will
    be created.
