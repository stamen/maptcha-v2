SimpleDB
========

Atlases
-------

 * `href`: Original source URL of uploaded CSV file.
 * `status`: currently one of *empty*, *uploaded*.
 * `timestamp`: Numeric Unix epoch upload time.
 * `title`: Librarian-supplied title string.
 * `affiliation`: Librarian-supplied affiliation string.
 * `map_count`: Number of maps included in this atlas.

SimpleDB domain: *prefix* + “-atlases”

Maps
----

 * `atlas`: SimpleDB key for enclosing Atlas.
 * `image`: S3 object ID of raw uploaded image.
 * `large`: S3 object ID of large-sized image.
 * `thumb`: S3 object ID of thumbnail-sized image.
 * `ul_lat`: Latitude of upper-left map corner consensus.
 * `ul_lon`: Longitude of upper-left map corner consensus.
 * `lr_lat`: Latitude of lower-right map corner consensus.
 * `lr_lon`: Longitude of lower-right map corner consensus.
 * `status`: currently one of *empty*, *finished* (uploaded).
 * `aspect`: Numeric aspect ratio, width/height.

In addition, all values supplied during upload in the CSV file will be prefixed
with “__” and included as free-form attributes.

SimpleDB domain: *prefix* + “-maps”

Rough Placements
----------------

 * `map`: SimpleDB key for connected Map.
 * `timestamp`: Integer literal Unix timestamp.
 * `ul_lat`: Latitude of upper-left map corner.
 * `ul_lon`: Longitude of upper-left map corner.
 * `lr_lat`: Latitude of lower-right map corner.
 * `lr_lon`: Longitude of lower-right map corner.

SimpleDB domain: *prefix* + “-rough_placements”

Task Queue
==========

Queue name: *prefix* + “jobs”

`populate atlas nnnnnn`
-------------------------------

Causes a CSV to be retrieved from the atlas `href` and converted to a set of
maps. Atlas is identified by name (*nnnnnn*).
