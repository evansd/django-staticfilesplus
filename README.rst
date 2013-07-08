Django StaticfilesPlus
======================

A tiny library that adds asset pre-processor support to Django's `contrib.staticfiles`.

The bundled `contrib.staticfiles` does most of what I want from an asset manager, but not
quite all. Rather than replace it entirely with another asset manager, I wrote this little
hack to add the missing piece. Now assets that need pre-processing (like LESS stylesheets,
or Sprocketized JS files) get compiled dynamically in development and then written out as
static files for serving in production.

Features:

 * Seamleess integration with `contrib.staticfiles`: Continue to use the ``static``
   template tag and ``collectstatic`` command as normal.
 * Ships with support for LESS stylesheets and Sprockets-like JavaScript concatenation and
   minification.
 * Very simple API for defining new pre-processors.
 * Not a single line of my code needs to run in production: once you've run
   ``collectstatic``, its work is done.

Read the documentation: http://django-staticfilesplus.evans.io
