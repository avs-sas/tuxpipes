#!/bin/bash

# intro
echo "This is a tutorial for tuxpipes"
echo -e "\t Best to run it from the tuxpipes main directory"
echo -e "\t This will not work if you install it via recipe on a target yet (WIP)"
echo -e "\t If you want to test it on a target you need to copy the repo to the target"
# asked user if they want to continue
echo "Do you want to continue? (y/n)"
read answer
if [ $answer != "y" ]; then
    echo "Exiting..."
    exit 1
fi

echo "Let's start with a simple example..."

# create a pipes
echo "----------"
echo "First we create a simple pipeline to display a test image"
echo ""
echo "This is how the most basic GStreamer pipeline looks like:"
echo -e "\n\t gst-launch-1.0 videotestsrc ! autovideosink"
echo ""
echo "They always start with 'gst-launch-1.0' followed by any number of elements separated by ' ! '"
echo "It is important to use spaces before and after the ' ! '"
echo "Everything inside a pipeline element belongs together. There can be options and properties"
echo "Every pipeline needs to end with a sink element"
echo "In this case we use the 'autovideosink' element"

# ask if user wants to run the pipeline
echo ""
echo "Do you want to run the pipeline? (y/n)"
echo -e "\n\t press ctrl+c or close the window to stop the pipeline"
read answer
if [ $answer = "y" ]; then
    gst-launch-1.0 videotestsrc ! autovideosink
fi
# set sink variable to autovideosink
sink="autovideosink"

# ask the user if the pipeline worked
echo ""
echo "Did the pipeline work? (y/n)"
read answer
if [ $answer != "y" ]; then
    echo "Lets try another sink"
    echo "This time we use the 'waylandsink"
    gst-launch-1.0 videotestsrc ! waylandsink
    sink="waylandsink"
    # ask the user if the pipeline worked
    echo ""
    echo "Did the pipeline work? (y/n)"
    read answer
    if [ $answer != "y" ]; then
        # ask the user to choose a sink
        echo "Please enter a sink element:"
        read sink
    fi
fi

# print current sink
echo ""
echo "We use this sink from now on: $sink"
# Press any key to continue
read -n 1 -s -r -p "Press any key to continue"

echo ""
echo "If you want to change the size of the output window you need to set it"
echo "This can be done by using the 'video/x-raw' element"
echo "The 'video/x-raw' element properties for width and height."
echo "You set them like this:"
echo -e "\n\t gst-launch-1.0 videotestsrc ! video/x-raw,width=640,height=480 ! $sink"

# ask the user if they want to run the pipeline
echo ""
echo "Do you want to run the pipeline? (y/n)"
read answer
if [ $answer = "y" ]; then
    gst-launch-1.0 videotestsrc ! video/x-raw,width=640,height=480 ! $sink
fi

echo ""
echo "Now we want to add the testsrc pipeline to tuxpipes."
echo "But we leave out the gst-launch-1.0 part and the sink, you will see why later"
echo "To add it we use the '--add' command. The looks like this:"
echo -e "\n\tpython3 tuxpipes.py --add tut_testsrc:videotestsrc:video/x-raw,width=640,height=480"
echo ""
echo "As you might see, we replace the ' ! ' with a ':'"
echo "The first part is the name of the pipeline, followed by elements separated by ':'"

# ask the user if they want to add the pipeline
echo ""
echo "Do you want to add the pipeline? (y/n)"
read answer
if [ $answer = "y" ]; then
    python3 tuxpipes.py --add tut_testsrc:videotestsrc
fi

echo ""
echo "The pipeline should be added now"
echo "You can check it by running 'python3 tuxpipes.py --list'"
echo "You can also filter the output like this:"
echo -e "\n\tpython3 tuxpipes.py --list tut"
python3 tuxpipes.py --list tut

# Press any key to continue
read -n 1 -s -r -p "Press any key to continue"

echo ""
echo "Lets now stream a video file to the display"
echo "We use the 'filesrc' element to read the file"
echo "The 'decodebin' element is used to decode the file"
echo "The 'videoconvert' element is used to convert the video to a format that can be displayed"
echo "The 'video/x-raw' element is used to set the display size"
echo -e "\n\t gst-launch-1.0 filesrc location=./files/avs720qb.avi ! decodebin ! videoconvert ! video/x-raw,width=640,height=480 ! $sink"

# ask the user if they want to run the pipeline
echo ""
echo "Do you want to run the pipeline? (y/n)"
read answer
if [ $answer = "y" ]; then
    gst-launch-1.0 filesrc location=./files/avs720qb.avi ! decodebin ! video/x-raw,width=640,height=480 ! videoconvert ! $sink
fi

echo ""
echo "Now we want to add the video pipeline to tuxpipes."
echo "But like before we leave out some parts"

python3 tuxpipes.py --add "tut_video:filesrc location=./files/avs720qb.avi:decodebin:videoconvert"

# Press any key to continue
read -n 1 -s -r -p "Press any key to continue"

echo ""
echo "Now comes a big one. Instead of displaying one source at a time we want to display multiple sources."
echo "For this we use the 'compositor' element"
echo "The 'compositor' element is used to combine multiple sources into one output"
echo "This is the pipeline we want to use:"
echo -e "\n\t gst-launch-1.0 compositor name=c sink_0::xpos=0 sink_0::ypos=0 sink_0::width=960 sink_0::height=540 sink_0::keep-ratio=true sink_1::xpos=960 sink_1::ypos=0 sink_1::width=960 sink_1::height=540 sink_1::keep-ratio=true sink_2::xpos=0 sink_2::ypos=540 sink_2::width=960 sink_2::height=540 sink_2::keep-ratio=true sink_3::xpos=960 sink_3::ypos=540 sink_3::width=960 sink_3::height=540 sink_3::keep-ratio=true ! autovideosink videotestsrc ! c.sink_0 videotestsrc ! c.sink_1 videotestsrc ! c.sink_2 videotestsrc ! c.sink_3"

echo ""
echo "Dont worry, this looks more complicated than it is."
echo "The start of the pipeline is the same as before,"
echo "but instead of a source, we use the 'compositor' element and define a name for it with 'name=c'"
echo ""
echo "After that, we define 4 sinks for the compositor buy using 'sink_0', 'sink_1', 'sink_2' and 'sink_3'"
echo "We set the position of the sink with 'xpos' and 'ypos' and the size with 'width' and 'height'"
echo "We also set 'keep-ratio=true' to keep the aspect ratio of the source"
echo "After that we define the sink with ' ! $sink'"
echo "Last but not least we add the sources to the compositor sinks"
echo "Here we use 4 videotestsrc elements"

# ask the user if they want to run the pipeline
echo ""
echo "Do you want to run the pipeline? (y/n)"
read answer
if [ $answer = "y" ]; then
    gst-launch-1.0 compositor name=c sink_0::xpos=0 sink_0::ypos=0 sink_0::width=960 sink_0::height=540 sink_0::keep-ratio=true sink_1::xpos=960 sink_1::ypos=0 sink_1::width=960 sink_1::height=540 sink_1::keep-ratio=true sink_2::xpos=0 sink_2::ypos=540 sink_2::width=960 sink_2::height=540 sink_2::keep-ratio=true sink_3::xpos=960 sink_3::ypos=540 sink_3::width=960 sink_3::height=540 sink_3::keep-ratio=true ! autovideosink videotestsrc ! c.sink_0 videotestsrc ! c.sink_1 videotestsrc ! c.sink_2 videotestsrc ! c.sink_3
fi

echo ""
echo "Lets add this pipeline to tuxpipes"
echo "But we use a new feature of tuxpipes. We use variables for the sources, so we can set them later"
echo -e "\n\t python3 tuxpipes.py --add tut_compositor:compositor name=c sink_0::xpos=0 sink_0::ypos=0 sink_0::width=960 sink_0::height=540 sink_0::keep-ratio=true sink_1::xpos=960 sink_1::ypos=0 sink_1::width=960 sink_1::height=540 sink_1::keep-ratio=true sink_2::xpos=0 sink_2::ypos=540 sink_2::width=960 sink_2::height=540 sink_2::keep-ratio=true sink_3::xpos=960 sink_3::ypos=540 sink_3::width=960 sink_3::height=540 sink_3::keep-ratio=true ! autovideosink #SRC0= ! sink_0 #SRC1= ! sink_1 #SRC2= ! sink_2 #SRC3= ! sink_3" 

echo ""
echo "Variables always start with a '#' followed by the name of the variable followed by a '='"
echo "You can add a default value after the '=' but you dont have to"

# add the pipeline to tuxpipes
python3 tuxpipes.py --add "tut_compositor:gst-launch-1.0 compositor name=c sink_0::xpos=0 sink_0::ypos=0 sink_0::width=960 sink_0::height=540 sink_0::keep-ratio=true sink_1::xpos=960 sink_1::ypos=0 sink_1::width=960 sink_1::height=540 sink_1::keep-ratio=true sink_2::xpos=0 sink_2::ypos=540 sink_2::width=960 sink_2::height=540 sink_2::keep-ratio=true sink_3::xpos=960 sink_3::ypos=540 sink_3::width=960 sink_3::height=540 sink_3::keep-ratio=true ! autovideosink #SRC0= ! c.sink_0 #SRC1= ! c.sink_1 #SRC2= ! c.sink_2 #SRC3= ! c.sink_3"

# Press any key to continue
read -n 1 -s -r -p "Press any key to continue"

echo ""
echo "Before we run it, let me quickly add two more pipelines to tuxpipes"
echo "One to use a camera as a source and one to use an image"
# ask the user to enter the video device
echo ""
echo "Please enter the video device of your camera (e.g. /dev/video0)"
read device
# if the user did not enter a device, set device to /dev/video0
if [ -z $device ]; then
    device="/dev/video0"
fi
# add the camera pipeline to tuxpipes
python3 tuxpipes.py --add "tut_camera:v4l2src device=$device:video/x-raw,width=640,height=480:videoconvert"

python3 tuxpipes.py --add "tut_image:filesrc location=./files/Avnet_Silica_SaS.png:pngdec:imagefreeze:videoconvert"

echo ""
echo "Ok, now lets check what pipelines we have in tuxpipes"
echo -e "\n\t python3 tuxpipes.py --list tut"

python3 tuxpipes.py --list tut

# Press any key to continue
read -n 1 -s -r -p "Press any key to continue"

echo ""
echo "Now we can combine our pipelines to fill the compositor we created"
echo "for this, we just need to set the variables. We use the source pipelines we created to fill the compositor"
echo "Variables are defined by adding brackets after the name of a pipeline"
echo "In the brackets you can define the variables you want to set, separated by a semicolon"
echo "The variables are defined by the name of the variable (with #) followed by a '=' and the value"
echo "or you just go from left to right (you can also combine both ways)"
echo "Our command looks like this:"
echo -e "\n\t python3 tuxpipes.py 'tut_compositor(tut_testsrc;#SRC2=tut_camera;tut_image;tut_video)'"

# ask the user if he wants to run the pipeline
echo ""
echo "Do you want to run the pipeline? (y/n)"
read answer
if [ $answer = "y" ]; then
    python3 tuxpipes.py "tut_compositor(tut_testsrc;#SRC2=tut_camera;tut_image;tut_video)"
fi

echo ""
echo "You can delete a pipeline with the following command:"
echo -e "\n\t python3 tuxpipes.py --delete tut_compositor"
echo ""
echo "That's it for this tutorial."
