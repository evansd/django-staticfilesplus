Processors
==========

Processors are responsible for processing static files: rewriting the content and
optionally changing the name.

StaticfilesPlus ships with a couple of default processors:

.. toctree::
   :maxdepth: 1

   javascript
   less

Writing your own processor
--------------------------

The processor API is very simple. For example, here is how you might write a processor
to handle CoffeeScript files:

.. code-block:: python

   from subprocess import check_call
   from staticfilesplus.processors import BaseProcessor

   class CoffeeScriptProcessor(BaseProcessor):
       original_suffix = '.coffee'
       processed_suffix = '.js'

       def process_file(self, input_path, output_path):
           with open(input_path, 'rb') as infile:
               with open(output_path, 'wb') as outfile:
                   check_call(['coffee', '--stdio'], stdin=infile, stdout=outfile)


API
~~~
A valid processor is class that implements the following set of methods.

First, we have a pair of methods which are given filenames and determine which files
the processor will operate on:

.. method:: get_original_name(name)

   Takes a processed filename and returns the original filename (which may be
   the same if the processor doesn't alter filenames) or ``None`` if the processor
   doesn't handle this type of file.

   For example, the ``LESSProcessor`` matches any string with a ``.css`` extension
   and returns it with a ``.less`` extension. The ``JavaScriptProcessor`` matches
   any string with a ``.js`` extension and returns it unchanged.

.. method:: get_processed_name(name)

   The reverse of the above method. Takes the original filename and returns the
   file name after processing (which can be the same) or ``None`` if the processor
   doesn't handle this type of file.

Then we have the method which does the actual processing of the file:

.. method:: process_file(input_path, output_path):

   Takes the file given by ``input_path``, processes it and writes it to ``output_path``.

Finally, we have:

.. method:: is_ignored_file(name):

   Takes a filename (before processing) and returns a Boolean. If it returns ``True`` the
   file will be ignored by ``contrib.staticfiles`` as if it did not exist.


BaseProcessor
~~~~~~~~~~~~~

A convenient base class is provided in ``staticfilesplus.processors.BaseProcessor``

.. code-block:: python

  class BaseProcessor(object):
      original_suffix = None
      processed_suffix = None

      def get_original_name(self, name):
          if name.endswith(self.processed_suffix):
              return name[:-len(self.processed_suffix)] + self.original_suffix

      def get_processed_name(self, name):
          if name.endswith(self.original_suffix):
              return name[:-len(self.original_suffix)] + self.processed_suffix

      def is_ignored_file(self, path):
          return False

      def process_file(self, input_path, output_path):
          raise NotImplementedError()
