********
tuxpipes
********

This script is intended to simplify working with GStreamer/GStreamer 
pipelines (gst-launch-1.0).
The main idea is to create pipelines more easily and to be able to 
reuse them by calling them with the given name. Also, it is possible 
to create pipelines with variables, which can be set by the user to 
modify existing pipelines.

Installation
============

If you just want to test and use the script, clone the repo and execute
it.
    
        $ git clone ...

        $ cd tuxpipes
        
        $ python tuxpipes.py -h


If you want to use it in a yocto project, you can add the recipe in

        tuxpipes -> yocto -> recipes-sas -> tuxpipes -> tuxpipes.bb

to your own layer.


The recipe will just copy the tuxpipes.py to 

        $ /usr/bin/tuxpipes

and makes it executable.

The pipes.json and settings.json will be copied to

        $ /etc/tuxpipes/

Usage
=====
Check the documentation under

        tuxpipes -> docs -> html -> index.html

