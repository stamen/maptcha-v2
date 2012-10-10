SimpleDB
========

Atlases
-------

 * `href`: Original source URL of uploaded CSV file.
 * `status`: currently one of *empty*, *uploaded*.

SimpleDB domain: *prefix* + “-atlases”

Maps
----

 * `atlas`: SimpleDB key for enclosing Atlas.
 * `image`: S3 object ID of raw uploaded image.
 * `large`: S3 object ID of large-sized image.
 * `thumb`: S3 object ID of thumbnail-sized image.

SimpleDB domain: *prefix* + “-maps”

Task Queue
==========

Queue name: *prefix* + “jobs”

`populate atlas nnnnnn`
-------------------------------

Causes a CSV to be retrieved from the atlas `href` and converted to a set of
maps. Atlas is identified by name (*nnnnnn*).
