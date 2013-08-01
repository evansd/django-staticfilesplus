JavaScript Processor
====================

This adds support for Sprockets_-like dependancy management for JavaScript files.

Dependencies between files are specified by specially formatted comments (known as
directives) at the top of the files. The processor compiles all these dependencies
together into a single file.

Activating
----------

Ensure that the processor is in the list of enabled processors in ``settings.py``:

.. code-block:: python

  STATICFILESPLUS_PROCESSORS = (
      ...
      'staticfilesplus.processors.js.JavaScriptProcessor',
      ...
  )


Directives
----------

The directive processor scans for comment lines beginning with = in comment blocks at the
top of the file.

.. code-block:: javascript

   //= require jquery
   //= require lib/myplugin.js

The first word immediately following = specifies the directive name. Any words following
the directive name are treated as arguments. Arguments may be placed in single or double
quotes if they contain spaces, similar to commands in the Unix shell.

**Note:** Non-directive comment lines will be preserved in the final asset, but directive
comments are stripped after processing. The processor will not look for directives in
comment blocks that occur after the first line of code.

The directive processor understands comment blocks in three formats:

.. code-block:: javascript

   /* Multi-line comment blocks (CSS, SCSS, JavaScript)
    *= require foo
    */

   // Single-line comment blocks (SCSS, JavaScript)
   //= require foo

   # Single-line comment blocks (CoffeeScript)
   #= require foo

Directives are comments of the form:

.. code-block:: javascript

   /*
   *= <directive> <path>
   */

   // ... OR ...

   //= <directive> <path>


Path arguments are parsed like shell arguments so they can be unquoted if they contain no special
characters (like spaces) or surrounded with single or double quotes.

To maintain compatibilty with Sprockets you can omit the ``.js`` extension from paths,
but I prefer to be explicit and include the extension.




.. code-block:: javascript

   /*
   *= <directive> <filename>
   */

   // ... OR ...

   //= require <filename>

Currently, we only support two of the standard Sprockets directives:

**require** <\ *filename*\ >
  Includes the content of the specified file, if it hasn't already been included.
  Note: processing is recursive so that directives in required files are themselves
  processed.

**stub** <\ *filename*\ >
  Marks the specified file (and all its dependencies) as not for inclusion, even if they are
  required by other directives. This is useful when you have multiple scripts on a page
  which may share dependencies and you want to ensure that the common dependencies only get
  included once. (There's no need to manually work out what the common dependencies are, just
  stub the entire file.)

.. code-block:: javascript

   /*
   * 
   *= require some-library
   *= require you-can-explicily-specify-extension.js
   */

   //= require "quoting works just like in shell"
   //= require ./paths/starting/with-a-dot/are-relative.js


Hidden files
------------

The JavaScript processor ignores all files and directories which **start with an underscore**.

These files can still be *require*\ d by other JavaScript files, but they will not be
individually included in the list of compiled files. This allows you to prevent
library files from being compiled as stand-alone files.

I tend to put library files in a directory called ``_lib`` for this reason.


Processing with Django template engine
--------------------------------------

Files with the extension ``.djtmpl.js`` will be first processed by Django's templating
engine. You should use this feature sparingly (it's quite a nasty hack) but it can help
to avoid repeating configuration values (particularly your URL config) in both Python
and JavaScript.

In the example below, ``config.djtmp.js`` pulls in a couple of values from Django's
configuration and then ``application.js`` `requires` it and uses those values.

.. code-block:: javascript

   /* application.js */

   //= require config.djtmpl.js
   $.ajax(URLS.my_endpoint);
   console.log(SETTINGS.title);


.. code-block:: javascript

   /* config.djtmpl.js */

   var URLS = {
      my_endpoint: "{% url  'my_endpoint '%}"
   };

   var SETTINGS = {
      title: "{{ settings.SOME_TITLE }}"
   };


.. _Sprockets: https://github.com/sstephenson/sprockets#the-directive-processor
