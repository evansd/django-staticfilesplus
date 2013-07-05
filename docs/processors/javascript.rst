JavaScript Processor
====================

This adds support for Sprockets_-like dependancy management for JavaScript files.

Usage
-----

Ensure that the processor is in the list of enabled processors in ``settings.py``:

.. code-block:: python

  STATICFILESPLUS_PROCESSORS = (
      ...
      'staticfilesplus.processors.js.JavaScriptProcessor',
      ...
  )

Processing with Django template engine
--------------------------------------

Files with the extension ``.djtmpl.js`` will be first processed by Django's templating
engine. You should use this feature sparingly (it's quite a nasty hack) but it can help
to avoid repeating configuration values (particularly your URL config) in both Python
and JavaScript.

For example:

.. code-block:: javascript

   // application.js

   //= require config.djtmpl.js
   $.ajax(URLS.my_endpoint);
   console.log(SETTINGS.title);


.. code-block:: javascript

   // config.djtmpl.js
   var URLS = {
      my_endpoint: "{% url  'my_endpoint '%}"
   };

   var SETTINGS = {
      title: "{{ settings.SOME_TITLE }}"
   };


.. _Sprockets: https://github.com/sstephenson/sprockets#the-directive-processor
