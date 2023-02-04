pipes.json
==========

The pipes.json file contains all known/added pipelines.
It is located either in the same directory as tuxpipes.py
or in under /etc/tuxpipes/pipes.json.

This is an example entry of the pipes.json file.

.. code-block:: json
   :caption: example

    {
        "example": {
            "input": "example:gstdev:vidxraw720:#CONVERTER=videoconvert:#SINK=waylandsink",
            "tuxpipe": "gst-launch-1.0 v4l2src device=/dev/video#DEVNUM=3 #OPTIONS=:video/x-raw,width=#WIDTH=720,height=#HEIGHT=480,framerate=#FRAMERATE=20/1:#CONVERTER=videoconvert:#SINK=waylandsink",
            "elements": [
                "gst",
                "videoxraw720",
                "#CONVERTER=videoconvert",
                "#SINK=waylandsink",
            ],
            "variables": {
                "#DEVNUM": "3",
                "#OPTIONS": "",
                "#WIDTH": "720",
                "#HEIGHT": "480",
                "#FRAMERATE": "20",
                "#CONVERTER": "videoconvert",
                "#SINK": "waylandsink",
            },
            "subpipelines": ["gst", "vidxraw720"],
        }
    }

The **input** string is the pipe string added by the user.

The **tuxpipe** ist just the same without the name at the beginning.

The **elements** part is a list of elements. Separated by a ":" in the input string.

**variables** are marked with a leading "#" and followed by a "=". It is optional to add a default value after the "=".

The **subpipelines** part is a list of "known" elements. Those are other pipelines stored in the pipes.json.