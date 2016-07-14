+++++++++++++++
Developer Guide
+++++++++++++++

The primary use case for Flatten Tool is to convert spreadsheets to JSON so
that the data can be validated using a `JSON Schema
<http://json-schema.org/documentation.html>`_.

Flatten Tool has to be very forgiving in what it accepts so that it can deal
with spreadsheets that are a work-in-progress. It tries its best to make
sense of what you give it, even if you give it inconsistent, conflicting or
patchy data. It leaves the work of reporting problems to the JSON Schema
validator that will be run on the JSON it produces, and it only generates
warnings if it is forced to ignore data from the source spreadsheet.

Flatten Tool tries its best to output as much as it can so the JSON it produces
will be as good or bad as the spreadsheet input it receives. The benefit of
this approach that the user can be shown all the problems in one go when the
JSON Schema validator is run on that JSON.

Programming a very forgiving tool that tries to accept lots of categories of
errors is a lot more complex than programming a tool where the data structures
are very predictable. Understanding this intention not to raise errors is key
to understanding Flatten Tool's internal design.


Helper libraries
================

As you'll have read in the :doc:`User Guide <userguide>`, Flatten Tool makes
use of JSON Pointer, JSON Schema and JSON Ref standards. The Python libraries
that support this are `jsonpointer`, `jsonschema` and `jsonref` respectively.


Testing coverage of documentation examples
==========================================

.. code-block:: bash

    rm -f .coverage # Remove the old coverage if it exists
    python flattentool/tests/test_docs.py
    coverage combine
    coverage report --omit=flattentool/tests/**


What's coming up
================

Three layer design
------------------

The codebase will be refactored so that the unflatten part of the library comes
in three parts:

Spreadsheet Loaders

   Responsible for loading data out of spreadsheets and representing it in the
   correct format for the unflattener - a Python structure of basic JSON types and
   the special `Empty` value

Unflatten function

   Takes the Python data structure described above and unflattens it, using a
   JSON Schema if present and keeping all state explicit.

   Use the JSON Schema to convert any basic JSON types to richer types that can
   be correctly serailised by a serialiser later (e.g. dates). Returns a cell
   tree.

Serialisers

   Take a cell tree and serialise it to either a JSON tree, a source map, or both

This pattern will make it easier to support testing the core unflatten
function, as well as making it easier to support future spreadsheet and
serialiser formats.


Explicit float support
----------------------

The existing implementation makes a special effort to correctly handle decimal
types such as currency.

It will be important for the unflatten function to support the `float` type
explicitly, rather than treating it as a `Decimal` in order to make sure the
values are perfectly handled in JSON. This is due to this quirk of Python's
behaviour:

.. code-block:: python

   >>> from decimal import Decimal
   >>> Decimal('1.3') == Decimal(1.3)
   False
   >>> Decimal(1.3)
   Decimal('1.3000000000000000444089209850062616169452667236328125')


Clean up of code
----------------

Now that we are happy with the approach the code takes internally, we can
remove functions that we no longer need. In particular we can remove code
branches where `WITH_CELLS` is `False` because we are happy with the cell
source map implementation.


Stdin support
-------------

The next version could support a single sheet being fed into `stdin` like this:

.. code-block:: bash

   cat << EOF | flatten-tool unflatten -f=csv --root-list-path=cafe
   name,
   Healthy Cafe,
   EOF

More documentation
------------------

* Flattening, roll up and template creation
* Timezone support
* Using Flatten Tool as a library
* Source maps

Naming and Versioning
---------------------

The next release of Flatten Tool will likely start a version numbering schema.
We could also name the command line tool `flattentool` rather than
`flatten-tool` so that everything is consistent.

Other possible directions
-------------------------

It might be also be good to add a `CHANGELOG.txt` which could document changes
such as:

* This documentation
* Changed stdout behaviour for unflatten and loss of the default - writing to
  `unflattened.json`.
* Publishing on PyPi