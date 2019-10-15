## YaRSS2 : Yet another RSS 2, a RSS plugin for Deluge ##

Author: Bro <bro.development@gmail.com>

Based on YaRSS by Camillo Dell'mour

License: GPLv3

## Building the plugin ##

```
#!bash

$ python setup.py bdist_egg
```


## Running the tests ##
The directory containing yarss2 must be on the PYTHONPATH

e.g.

```
#!bash

yarss2$ export PYTHONPATH=$PYTHONPATH:$PWD/..
```


Run the tests with:

```
#!bash

yarss2$ trial tests
```
