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

Usage:
======
The program expects at least one option/argument or an input_string
(pipeline)

        "python tuxpipes.py [options] [input_string]"

        "tuxpipes [options] [input_string]"

Syntax
======

The syntax for a tuxpipe pipeline is as follows:

        <name>:<element1>:<element2>:...:<elementN>

The name is used to call the pipeline or use it in another pipeline.
The elements can basically be everything -  other pipelines, gstreamer
elements or just placeholder variables.

Variables inside pipes begin with an "#" followed by the name followed by 
an "=" followed by an optional default value.

        #<name>=<default value>

To set the value for the variable when calling the pipeline add a bracket
element after the actual pipeline.

        <pipeline_name>(720,480,#FRAMERATE=30,#DEVICENUM=3)

The values are separated by a comma. The script first tries to set all 
specific variables and then goes from left to right.

Examples:
=========
gst:

        "gst:gst-launch-1.0 #OPTIONS="

device:

        "dev:v4l2src device=/dev/video#DEVNUM=3"

gstdev:

        "gst:gst-launch-1.0 v4l2src device=/dev/video#DEVNUM=3 #OPTIONS="

vidxraw720:

        "vidxraw720:video/x-raw,width=#WIDTH=720,height=#HEIGHT=480,framerate=#FRAMERATE=20/1"

example:

        "example:gstdev:vidxraw720:#CONVERTER=videoconvert:#SINK=waylandsink"

Options:
========
-h, --help      Show the help message and exit

-a, --add  <input_string>       Add a new pipeline

-d, --delete <pipe_name>        Delete a pipeline

-r, --rename <old_name new_name>        Rename a pipeline

-l, --list <filter>     List all pipelines

-i, --info <pipe_name>  Show information about a pipeline

-o, --output <pipe_name>        Create an output file containing the pipeline command

-y, --yes       Answer yes to all questions

-n, --no        Answer no to all questions

-c, --commands <FILENAME>       Specify a pre commands file (executed before the pipeline)


For all command line options call -h / --help or check the docs.

        tuxpipes -> docs -> html -> index.html