LESS Processor
=================

This adds support for LESS_, the extended CSS dialect.

Usage
-----

.. note:: You'll need to install the LESS compiler. See the section on `Server-side Usage`
          in the `LESS documentation`_

Ensure that the processor is in the list of enabled processors in ``settings.py``:

.. code-block:: python

  STATICFILESPLUS_PROCESSORS = (
      ...
      'staticfilesplus.processors.less.LESSProcessor',
      ...
  )

In your templates, link to your LESS files using their post-processed ``.css`` extension,
not their original  ``.less`` extension. For example:

.. code-block:: css

  /* myapp/static/styles.less */
  p {
    color: green;
  }


.. code-block:: html

  <!-- myapp/templates/base.html -->
  ...
  <link rel="stylesheet" href="{% static 'styles.css' %}" type="text/css"/>
  ...


Hidden files
------------

The LESS processor ignores all files and directories which **start with an underscore**.

LESS itself can still `@import` these files but they will not be individually included in
the list of compiled files. This allows you to prevent library files from being compiled as
stand-alone files, which will often break anyway if these files rely on variables that have not
been defined.

For example, in this case:

.. code-block:: css

  /* myapp/static/styles.less */
  @import '_lib/base.less';
  
  h1 {
    background-color: blue;
  }

.. code-block:: css

  /* myapp/static/_lib/base.less */
  p {
    color: green;
  }
  ...

The final output would contain a ``styles.css`` file (with the imported content of
``base.less``) but no stand-alone ``_lib/base.css`` file.


Settings
--------

.. attribute:: STATICFILESPLUS_LESS_COMPRESS

    :default: the opposite of ``DEBUG``

    Passes the ``--compress`` flag to the LESS compiler to produce minified output suitable
    for production.

.. _LESS: http://lesscss.org/
.. _`LESS documentation`: http://lesscss.org/#usage
