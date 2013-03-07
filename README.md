Year of the Bay
===============

YOTB is a map warping tool based on Maptcha and Stamen's previous work with
NYPL/Stanford. Stamen has developed an independent application tailored to the
needs of map collections, focusing on both the rectification interface and the
selection process. It’s possible for Year Of The Bay editors to decide which
historic maps and atlases are a priority for rectification, and guide the
public toward just those maps. It’s simple for visitors to perform piecemeal,
rapid, repetitive tasks to help, with simple scale and rotation controls
skipping much of the GIS complexity of more complex rubbersheeting
applications. We think this will allow the maximum number of participants to
make the most meaningful impact on the collections.

The four API touchpoints below address Historypin’s desire to keep the map
feature connected to their site, and make the end results available in a form
that’s maximally compatible with their potential needs.

Uploading Maps
--------------

There are 4 basic steps to uploading a set of maps to YOTB:

**Select a set of historical maps.**

Choose the maps you'd like to upload to YOTB, and place the digital versions
somewhere public on the web. Public here just means somewhere online that isn't
password-protected. (We call this set of maps an atlas, even though it may not
actually be one in real life.)
 
**Create a spreadsheet that describes each of the maps.**

You'll need a row in the spreadsheet for each map. You'll also need to save the
spreadsheet in CSV format, then upload it somewhere public on the web. There's
a service called Dropbox that is handy for this sort of thing. See below for
more information on what you need to include in the CSV.
 
**Tell YOTB where that spreadsheet is.**

Use the form a [yotb.stamen.com/upload](http://yotb.stamen.com/upload) to point
YOTB at the CSV file's URL, and hit Next.
 
**Provide some simple geographical hints about the atlas.**

Like, any particular map features (street-level, coastlines etc) and for
city-name clues to help determine a bounding box that contains all the maps in
the atlas. This will come in handy later, for volunteers who are placing the
maps to begin in the right general area.

Getting Links To Editable Maps
------------------------------

YOTB provides a list of maps in JSON form at
[yotb.stamen.com/maps](http://yotb.stamen.com/maps). Historypin should use this
feature to generate listings on a page, treating YOTB as an external service.

Show Visitors A Single Map To Place
-----------------------------------

We have an interface written in Javascript and HTML to allow visitors to
rectify a single map, visible at URLs like
`http://yotb.stamen.com/place-rough/map/{map ID}`. This interface is suitable
for presentation in an iFrame, with Historypin framing around it to provide
context.

Map Tile For Use In Historypin
------------------------------

Georectified map data is available in the form of web mercator map tiles,
compatible with the majority of web mapping libraries including Google, Bing,
Leaflet, OpenLayers and other similar tools. These tiles can be integrated
using URLs like `yotb.stamen.com/tile/map/{map ID}/{z}/{x}/{y}.png`, and
previewed at URLs like `yotb.stamen.com/map-sandwich/map/{map ID}`.

Installation
============

Despite the AWS dependencies, the actual web server and workers do not need to
run on EC2.  You will need an [Amazon Web Services](http://aws.amazon.com)
account. Once you've got that sorted, choose a prefix (`yotb_`, for example)
and create the following SQS queues:

* `{prefix}create`
* `{prefix}tile`
* `{prefix}jobs`

You'll also need to create an S3 bucket: `{prefix}stuff`

`init-db.py` can do this for you:

```bash
$ python init-db.py <AWS_KEY> <AWS_SECRET> <prefix>
```

Edit `config.ini` with the prefix you chose as well as an [access key and
secret](https://portal.aws.amazon.com/gp/aws/securityCredentials).

Install required packages (this assumes Ubuntu 12.04):

```bash
$ sudo apt-get install -y gdal-bin nginx gunicorn mysql-server python-imaging \
  python-shapely python-mysql.connector python-boto python-werkzeug python-jinja2
```

Install Python modules (note: flask is available from apt, but the version
there isn't recent enough):

```bash
$ sudo pip install ModestMaps
$ sudo pip install flask
```

Create a MySQL database:

```bash
$ mysqladmin -u root create yotb
```

Import the schema:

```bash
$ mysql -u root yotb < Schema.mysql
```

Update `config.ini` with MySQL connection information (**don't check this in**):

```bash
$ sensible-editor config.ini
```

Run the Flask application using the `yotb.sh` script after placing it in
`/etc/init.d`. You'll need to change the path where `yearofthebay` is checked
out by changing the value for `DIRNAME`:

```bash
sensible-editor edit_ui/yotb.sh
sudo cp edit_ui/yotb.sh /etc/init.d
sudo /etc/init.d/yotb.sh start
```

You'll also need to configure `nginx` as a reverse proxy to connect to the
Flask application (this will overwrite nginx's default virtualhost):

```bash
sudo cp edit_ui/nginx.conf /etc/nginx/sites-available/default
sudo /etc/init.d/nginx restart
```

The editor UI will now be available at [http://localhost/](http://localhost/).

Finally, configure the workers to run out of cron.  The following snippet sets
up 3 workers.  They are run minutely as they (should) complete after 50s (and
include file locking to prevent more running than intended).  Paste it into
`/etc/crontab`:

```
* * * * *	ubuntu	/path/to/yearofthebay/worker/run.sh 1
* * * * *	ubuntu	/path/to/yearofthebay/worker/run.sh 2
* * * * *	ubuntu	/path/to/yearofthebay/worker/run.sh 3
```

```bash
sudo sensible-editor /etc/crontab
```

Adjust the number of processes according to system capacity and demand.
