#!/usr/bin/env python3
"""
tuxpipes
========

This script is intended to simplify working with GStreamer/GStreamer 
pipelines (gst-launch-1.0).
The main idea is to create pipelines more easily and to be able to 
reuse them by calling them with the given name. Also, it is possible 
to create pipelines with variables, which can be set by the user to 
modify existing pipelines.

Usage:
======
The program expects at least one option/argument or an input_string
(pipeline)

        "python tuxpipes.py [options] [input_string]"

        "tuxpipes [options] [input_string]"

Syntax:
=======
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

**Note:** Variables a quite limited. It only goes one layer deep for now!

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
-h, --help                          Show the help message and exit

-a, --add  <input_string>           Add a new pipeline

-d, --delete <pipe_name>            Delete a pipeline

-r, --rename <old_name new_name>    Rename a pipeline

-l, --list <filter>                 List all pipelines

-i, --info <pipe_name>              Show information about a pipeline

-o, --output <pipe_name>            Create an output file containing the pipeline command

-y, --yes                           Answer yes to all questions

-n, --no                            Answer no to all questions

-c, --commands <FILENAME>           Specify a pre commands file (executed before the pipeline)

"""

from argparse import ArgumentParser
from subprocess import call, Popen, run
import os
import sys
import re
import json

# Global variables
# ================
APPNAME = "tuxpipes"
VARIABLES = "variables"
ELEMENTS = "elements"
SUBPIPELINES = "subpipelines"
INPUT = "input"
TUXPIPE = "tuxpipe"

DEFAULT_PIPES = {
    "dev": {
        "input": "dev:v4l2src device=/dev/video#DEVNUM=3",
        "tuxpipe": "v4l2src device=/dev/video#DEVNUM=3",
        "elements": ["v4l2src device=/dev/video#DEVNUM=3"],
        "variables": {"#DEVNUM": 3},
        "subpipelines": [],
    },
    "file": {
        "input": "file:filesrc location=#PATH=",
        "tuxpipe": "filesrc location=#PATH=",
        "elements": ["filesrc location=#PATH="],
        "variables": {"#PATH": ""},
        "subpipelines": [],
    },
    "testsrc": {
        "input": "testsrc:videotestsrc pattern=#PATTERN=1",
        "tuxpipe": "videotestsrc pattern=#PATTERN=1",
        "elements": ["videotestsrc pattern=#PATTERN=1"],
        "variables": {"#PATTERN": 1},
        "subpipelines": [],
    },
    "gst": {
        "input": "gst:gst-launch-1.0 #OPTIONS=",
        "tuxpipe": "gst-launch-1.0 #OPTIONS=",
        "elements": ["gst-launch-1.0 #OPTIONS="],
        "variables": {"#OPTIONS": ""},
        "subpipelines": [],
    },
    "gstdev": {
        "input": "gst:gst-launch-1.0 v4l2src device=/dev/video#DEVNUM=3 #OPTIONS=",
        "tuxpipe": "gst-launch-1.0 v4l2src device=/dev/video#DEVNUM=3 #OPTIONS=",
        "elements": ["gst-launch-1.0 v4l2src device=/dev/video#DEVNUM=3 #OPTIONS="],
        "variables": {"#DEVNUM": 3, "#OPTIONS": ""},
        "subpipelines": [],
    },
    "gstfile": {
        "input": "gst:gst-launch-1.0 filesrc location=#PATH= #OPTIONS=",
        "tuxpipe": "gst-launch-1.0 filesrc location=#PATH= #OPTIONS=",
        "elements": ["gst-launch-1.0 filesrc location=#PATH= #OPTIONS="],
        "variables": {"#PATH": "", "#OPTIONS": ""},
        "subpipelines": [],
    },
    "gsttest": {
        "input": "gst:gst-launch-1.0 videotestsrc pattern=#PATTERN=1 #OPTIONS=",
        "tuxpipe": "gst-launch-1.0 videotestsrc pattern=#PATTERN=1 #OPTIONS=",
        "elements": ["gst-launch-1.0 videotestsrc pattern=#PATTERN=1 #OPTIONS="],
        "variables": {"#PATTERN": 1, "#OPTIONS": ""},
        "subpipelines": [],
    },
    "vidxraw720": {
        "input": "vidxraw720:video/x-raw,width=#WIDTH=720,height=#HEIGHT=480,framerate=#FRAMERATE=20/1",
        "tuxpipe": "video/x-raw,width=#WIDTH=720,height=#HEIGHT=480,framerate=#FRAMERATE=20/1",
        "elements": [
            "video/x-raw,width=#WIDTH=720,height=#HEIGHT=480,framerate=#FRAMERATE=20/1"
        ],
        "variables": {"#WIDTH": "720", "#HEIGHT": "480", "#FRAMERATE": "20"},
        "subpipelines": [],
    },
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
    },
    "composeLR": {
        "input": "composeLR:gst:#COMPOSITOR=compositor name=c sink_1::xpos=#XPOS1=0 sink_1::ypos=#YPOS1=0 sink_1::width=#WIDTH1=720 sink_1::height=#HEIGHT1=480 sink_2::xpos=#XPOS2=0 sink_2::ypos=#YPOS2=720 sink_2::width=#WIDTH2=720 sink_2::height=#HEIGHT2=480.#SINK=waylandsink #INPUTPIPE1= ! c.sink_1 #INPUTPIPE2=  ! c.sink2",
        "tuxpipe": "gst-launch-1.0 #OPTIONS=:#COMPOSITOR=compositor name=c sink_1::xpos=#XPOS1=0 sink_1::ypos=#YPOS1=0 sink_1::width=#WIDTH1=720 sink_1::height=#HEIGHT1=480 sink_2::xpos=#XPOS2=0 sink_2::ypos=#YPOS2=720 sink_2::width=#WIDTH2=720 sink_2::height=#HEIGHT2=480.#SINK=waylandsink #INPUTPIPE1= ! c.sink_1 #INPUTPIPE2=  ! c.sink2",
        "elements": [
            "gst-launch-1.0 #OPTIONS=",
            "#COMPOSITOR=compositor name=c sink_1::xpos=#XPOS1=0 sink_1::ypos=#YPOS1=0 sink_1::width=#WIDTH1=720 sink_1::height=#HEIGHT1=480 sink_2::xpos=#XPOS2=0 sink_2::ypos=#YPOS2=720 sink_2::width=#WIDTH2=720 sink_2::height=#HEIGHT2=480.#SINK=waylandsink #INPUTPIPE1= ! c.sink_1 #INPUTPIPE2=  ! c.sink2",
        ],
        "variables": {
            "#OPTIONS": "",
            "#COMPOSITOR": "compositor",
            "#XPOS1": "0",
            "#YPOS1": "0",
            "#WIDTH1": "720",
            "#HEIGHT1": "480",
            "#XPOS2": "0",
            "#YPOS2": "720",
            "#WIDTH2": "720",
            "#HEIGHT2": "480",
            "#SINK": "waylandsink",
            "#INPUTPIPE1": "",
            "#INPUTPIPE2": "",
        },
        "subpipelines": ["gst"],
    },
}

DEFAULT_SETTINGS = {"isDefault": True, "handleDupePipe": "ask", "blank": None}
# "gst-launch-1.0 -v imxcompositor_g2d name=c sink_0::xpos=0 sink_0::ypos=0 sink_0::width=960 sink_0::height=1080 sink_0::keep-ratio=true sink_1::xpos=960 sink_1::ypos=0 sink_1::width=960 sink_1::height=1080 sink_1::keep-ratio=true ! waylandsink  v4l2src device=/dev/video3 ! video/x-raw,width=1920,height=1080,framerate=20/1 ! videoconvert ! c.sink_0 videotestsrc ! video/x-raw,width=1920,height=1080,framerate=20/1 ! videoconvert ! c.sink_1"

# Helpers
# =======
def colored(text, color, prefix=f" > {APPNAME}: "):
    """
    Prints a colored message.

    Parameters
    ----------
    text: str
        The text to print.
    color: str
        The color of the text.
    prefix: str
        The prefix of the text. (default: " > {APPNAME}: ")
    """
    # Get the color code
    color_code = {
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "reset": "\033[0m",
    }
    # if prefix is None, set it to an empty string
    if prefix is None:
        prefix = ""
    # Print the message
    print(f"{prefix}{color_code[color]}{text}{color_code['reset']}")


def success(message, prefix=f" > {APPNAME}: "):
    """
    Prints a success message.

    Quick wrapper for colored(). (color: "green")

    Parameters
    ----------
    message: str
        The message to print.
    prefix: str
        The prefix of the message. (default: " > {APPNAME}: ")
    """
    colored(message, "green", prefix)


def attempt(message, prefix=f" > {APPNAME}: "):
    """
    Prints an attempt message.

    Quick wrapper for colored(). (color: "cyan")

    Parameters
    ----------
    message: str
        The message to print.
    prefix: str
        The prefix of the message. (default: " > {APPNAME}: ")
    """
    colored(message, "cyan", prefix)


def info(message, prefix=f" > {APPNAME}: "):
    """
    Prints an info message.

    Quick wrapper for colored(). (color: "white")

    Parameters
    ----------
    message: str
        The message to print.
    prefix: str
        The prefix of the message. (default: " > {APPNAME}: ")
    """
    colored(message, "white", prefix)


def warn(message, prefix=f" > {APPNAME}: "):
    """
    Prints a warning message.

    Quick wrapper for colored(). (color: "yellow")

    Parameters
    ----------
    message: str
        The message to print.
    prefix: str
        The prefix of the message. (default: " > {APPNAME}: ")
    """
    colored(message, "yellow", prefix)


def error(message, prefix=f" > {APPNAME}: "):
    """
    Prints an error message.

    Quick wrapper for colored(). (color: "red")

    Parameters
    ----------
    message: str
        The message to print.
    prefix: str
        The prefix of the message. (default: " > {APPNAME}: ")
    """
    colored(message, "red", prefix)


def header_message(message, color="green"):
    """
    Prints a header message.

    Clears the terminal and prints a header message.

    Parameters
    ----------
    message: str
        The message to print.
    color: str (default: "green")
        The color of the message.
    """
    # Get the length of the message
    length = len(message)
    # Clear the terminal
    # call("clear") skipped for now
    # Print the message in a box with the given color
    colored("+" + "-" * (length + 2) + "+", color, None)
    colored("| " + message + " |", color, None)
    colored("+" + "-" * (length + 2) + "+", color, None)


def create_default_path_dir(path):
    """
    Creates a directory at the given path.

    If the directory already exists, it does nothing.

    Parameters
    ----------
    path: str
        The path to create the directory at.
    """
    # If the directory does not exist, create it
    if not os.path.exists(path):
        os.makedirs(path)


def ask_yes_no(question):
    """
    Asks the user a yes/no question.

    Returns
    -------
    answer: bool
        True if the user answered yes, False if the user answered no.
    """
    # Ask the user the question
    answer = input(f"{question} [y/n] ")
    # If the user answered yes, return True
    if answer.lower() == "y":
        return True
    # If the user answered no, return False
    elif answer.lower() == "n":
        return False
    # If the user did not answer yes or no, ask the question again
    else:
        return ask_yes_no(question)


def create_parser():
    """
    Parses the command line arguments.

    Returns
    -------
    parser: ArgumentParser
        The ArgumentParser object.
    """
    parser = ArgumentParser()
    # basic arguement for calling a pipeline
    parser.add_argument(
        "input_string", nargs="?", help="Input format: PIPE_ELEMENT[:PIPE_ELEMENT]*"
    )
    # option for adding a new pipeline
    parser.add_argument(
        "-a",
        "--add",
        action="store_true",
        help="Add a new pipeline based on the input string",
    )
    # argument for deleting a pipeline
    parser.add_argument(
        "-d", "--delete", nargs=1, metavar="PIPELINE_NAME", help="Delete a pipeline"
    )
    # argument for renaming a pipeline
    parser.add_argument(
        "-r",
        "--rename",
        nargs=2,
        metavar=("OLD_NAME", "NEW_NAME"),
        help="Rename a pipeline",
    )
    # argument for listing all pipelines with optional filter
    parser.add_argument(
        "-l",
        "--list",
        nargs="?",
        metavar="FILTER",
        const="___",
        help="List all pipelines",
    )
    # option to show pipeline info based on the input string
    parser.add_argument(
        "-i",
        "--info",
        action="store_true",
        help="Show pipeline info based on the input string",
    )
    # argument to create a bash script for running a pipeline
    parser.add_argument(
        "-o",
        "--output",
        nargs="?",
        metavar="FILE_NAME",
        const="output.sh",
        help="Create a bash script for running a pipeline",
    )
    # options yes for all questions
    parser.add_argument(
        "-y", "--yes", action="store_true", help="Answer yes to all questions"
    )
    # option no for all questions
    parser.add_argument(
        "-n", "--no", action="store_true", help="Answer no to all questions"
    )
    # argument for setting a pre_command.json file
    # FIXME: Temporary added. Rework this.
    parser.add_argument(
        "-c",
        "--commands",
        nargs="?",
        metavar="FILE_NAME",
        const="pre_commands.json",
        help="Set a pre_commands.json file",
    )

    return parser

"""
Classes
=======
"""
class TuxPipes:
    """
    The main class of TuxPipes.

    It handles the pipelines and the variables.
    Also, it handles the execution of the pipelines,
    the creation of bash scripts and everything else.

    Attributes
    ----------
    input_string: str
        The input string for a tuxpipe pipeline.
    cwd: str
        The current working directory.
    pipes_json_path: str
        The path to the pipes.json file.
    settings_json_path: str
        The path to the settings.json file.
    default_path: str
        The default path to the pipes.json and settings.json files.
    pipes: dict
        A dictionary of all pipelines.
    settings: dict
        A dictionary of all settings.
    yes_flag: bool
        A flag to answer yes to all questions. (no > yes)
    no_flag: bool
        A flag to answer no to all questions. (no > yes)
    parser: ArgumentParser
        The ArgumentParser object.
    args: Namespace
        The parsed arguments.

    Methods
    -------
    check_files()
        Checks if the pipes.json and settings.json files exist.
    create_default_path_dir(path)
        Creates the default pipes.json file.
    read_pipes_json()
        Reads the pipes.json file and loads the pipelines.
    update_pipes_json()
        Updates the pipes.json file with the current pipelines.
    create_settings_json(path)
        Creates the default settings.json file.
    read_settings_json()
        Reads the settings.json file and loads the settings.
    split_pipename_and_pipestring(input_string)
        Splits the pipeline name and the pipeline string.
    create_pipeline_dict(pipe_name, pipe_string)
        Creates a dictionary of a pipeline.
    get_elements_and_subpipelines(pipe_string)
        Tries to find all elements and subpipelines in the pipe_string
    get_variables(tuxpipe)
        Finds all variables in the tuxpipe string.
    add_pipeline(input_string)
        Adds a new pipeline to the pipes.json file.
    remove_subpipelines(pipe_name, subpipeline)
        Removes a subpipeline from the pipeline.
    delete_pipeline(pipe_name)
        Deletes a pipeline from the pipes.json file.
    change_subpipe_name(pipe_name, subpipe_old_name, subpipe_new_name)
        Changes the name of a subpipeline in a pipeline.
    rename_pipeline(old_name, new_name)
        Renames a pipeline.
    list_pipelines(query=None)
        List available pipelines.
    show_pipeline_info(pipe_name)
        Shows the info of a known pipeline.
    create_output_file(pipe_string, output_file)
        Creates a bash script file for executing a pipeline.
    execute_commands(command, pre_commands=[], post_commands=[])
        Executes the commands of a pipeline.
    create_gstreamer_string(pipe_string)
        Creates a gstreamer string from the pipe_string.
    prepare_command_execution(gstreamer_string)
        Creates pre and post commands and does some pipeline checks.
    run_input_string(input_string)
        Directly runs a pipeline based on the input string.
    check_args()
        Checks for available command line arguments.
    """

    def __init__(self) -> None:
        """
        Initializes the TuxPipes object.
        """

        self.input_string = None
        self.cwd = os.getcwd()
        self.pipes_json_path = None
        self.settings_json_path = None
        self.default_path = "/etc/tuxpipes/"
        create_default_path_dir(self.default_path)
        self.check_files()
        self.pipes = {}
        self.pipes = self.read_pipes_json()
        self.settings = {}
        self.settings = self.read_settings_json()
        self.yes_to_all = False
        self.no_to_all = False
        self.parser = create_parser()
        self.args = self.parser.parse_args()

    def check_files(self):
        """
        Checks if the pipes.json and settings.json files exist.

        First it looks in the current working directory.
        If it does not find them there, it looks in the default path.
        If it does not find them there, it creates them.
        """

        if os.path.isfile("pipes.json"):
            self.pipes_json_path = os.path.join(self.cwd, "pipes.json")
        elif os.path.isfile(os.path.join(self.default_path, "pipes.json")):
            warn("No pipes.json file found in the current working directory.")
            self.pipes_json_path = os.path.join(self.default_path, "pipes.json")
            success("Found pipes.json file in the default path.")
        else:
            warn(f"No pipes.json file found in the default path. {self.default_path}")
            self.create_default_pipes_json(self.default_path)
            self.pipes_json_path = os.path.join(self.default_path, "pipes.json")
            success("Created pipes.json file in the default path.")
        if os.path.isfile("settings.json"):
            self.settings_json_path = os.path.join(self.cwd, "settings.json")
        elif os.path.isfile(os.path.join(self.default_path, "settings.json")):
            warn("No settings.json file found in the current working directory.")
            self.settings_json_path = os.path.join(self.default_path, "settings.json")
            success("Found settings.json file in the default path.")
        else:
            warn(
                f"No settings.json file found in the default path. {self.default_path}"
            )
            self.create_settings_json(self.default_path)
            self.settings_json_path = os.path.join(self.default_path, "settings.json")
            success("Created settings.json file in the default path.")
        print("\n")

    def create_default_pipes_json(self, path):
        """
        Creates the default pipes.json file.

        It will create the file at the given path
        and fill it with the DEFAULT_PIPES dictionary.

        Parameters
        ----------
        path: str
            The path to the pipes.json file.
        """
        # check if path ends with /
        if path[-1] != "/":
            path += "/"
        with open(path + "pipes.json", "w") as file:
            json.dump(DEFAULT_PIPES, file, indent=4)

    def read_pipes_json(self) -> dict:
        """
        Reads the pipes.json file and loads the pipelines.

        Returns
        -------
        pipes: dict
            A dictionary of all pipelines.
        """
        with open(self.pipes_json_path, "r") as file:
            pipes = json.load(file)
        return pipes

    def update_pipes_json(self):
        """
        Dumps the current pipelines to the pipes.json file.
        """
        with open(self.pipes_json_path, "w") as file:
            json.dump(self.pipes, file, indent=4)

    def create_settings_json(self, path):
        """
        Creates the settings.json file.

        It will create the file at the given path
        and fill it with the DEFAULT_SETTINGS dictionary.

        Parameters
        ----------
        path: str
            The path to the settings.json file.
        """
        # check if path ends with /
        if path[-1] != "/":
            path += "/"
        with open(path + "settings.json", "w") as file:
            json.dump(DEFAULT_SETTINGS, file, indent=4)

    def read_settings_json(self) -> dict:
        """
        Reads the settings.json file and loads the settings.

        # FIXME Not in use yet, so not implemented yet.
        Right now it just returns the default settings.

        Returns
        -------
        settings: dict
            A dictionary of all settings.
        """
        return DEFAULT_SETTINGS

    def split_pipename_and_pipestring(self, input_string: str) -> tuple:
        """
        Splits the pipeline name from the rest of the input string.

        Parameters:
        -----------
        input_string: str
            The input string to split.

        Returns:
        --------
        pipe_name: str
            The name of the pipeline.
        pipe_string: str
            The rest of the input string.
        """
        try:
            pipe_name, pipe_string = re.split(r"(?<!:):(?!:)", input_string, maxsplit=1)
        except:
            error(
                "Was not able to split the input string into a pipe name and a pipe string. - Check input format"
            )
            info("\tRequired format: pipe_name:element1[:element2]*", None)
            info("\t" + input_string, None)
            exit()
        return pipe_name, pipe_string

    def create_pipeline_dict(self, pipe_name: str, pipe_string: str) -> dict:
        """
        Creates a pipeline dictionary.

        It will create a dictionary with the given pipe name
        and the given pipe string.
        It will read all the elements from the pipe string
        to fill the dictionary.

        Parameters
        ----------
        pipe_name: str
            The name of the pipeline.
        pipe_string: str
            The pipeline string.

        Returns
        -------
        pipeline: dict
            A dictionary with the given pipe name and the given pipe string.
        """
        pipe = {}
        pipe[INPUT] = pipe_name + ":" + pipe_string
        elements, subpipelines = self.get_elements_and_subpipelines(pipe_string)
        pipe[ELEMENTS] = elements
        pipe[SUBPIPELINES] = subpipelines
        tuxpipe = ":".join(elements)
        pipe[TUXPIPE] = tuxpipe
        variables = self.get_variables(tuxpipe)
        pipe[VARIABLES] = variables
        return pipe

    def get_elements_and_subpipelines(self, pipe_string: str) -> tuple:
        """
        Tries to find all elements and subpipelines in the pipe string.

        It uses a regex to split the pipe string into elements
        which are separated by a single colon.
        "element1:element2:element3"
        r"(?<!:):(?!:)"

        All elements are added to the elements list.
        If an element is a known pipeline it will be added to the
        subpipelines list. (but only once)
        Also all elements of that subpipeline will be added to the
        elements list of the current pipeline.

        Parameters
        ----------
        pipe_string: str
            The pipeline string.

        Returns
        -------
        elements: list
            A list of all elements.
        subpipelines: list
            A list of all subpipelines.
        """
        # split by single colon
        parts = re.split(r"(?<!:):(?!:)", pipe_string)
        elements = []
        subpipelines = []
        for part in parts:
            if part in self.pipes:
                elements.extend(self.pipes[part][ELEMENTS])
                # Check if subpipeline is already in the list
                if part not in subpipelines:
                    subpipelines.append(part)
            else:
                elements.append(part)
        return elements, subpipelines

    def get_variables(self, tuxpipe: str) -> dict:
        """
        Finds all variables in the tuxpipe string.

        It uses a regex to find all variables and their default values.

        Parameters
        ----------
        tuxpipe: str
            The tuxpipe string.

        Returns
        -------
        variables: dict
            A dictionary of all variables and their default values.
        """
        variables = {}
        paris = re.findall(r"#.*?=[^(.|,|:|#| )]*.*?", tuxpipe)
        for pari in paris:
            variable, value = pari.split("=")
            variables[variable] = value
        return variables

    def add_pipeline(self, input_string: str):
        """
        Adds a pipeline to the pipes.json file.

        It will split the input string into a pipe name and a pipe string.
        Then it will create a pipeline dictionary with the pipe name and the pipe string.
        Then it will add the pipeline dictionary to the pipes dictionary.
        Then it will update the pipes.json file.

        If the pipeline which was overwritten was a subpipeline of another pipeline
        it will update the subpipelines list of that pipeline.

        Parameters
        ----------
        input_string: str
            The input string.
        """
        overwrite = False
        pipe_name, pipe_string = self.split_pipename_and_pipestring(input_string)
        # check if pipe already exists
        if pipe_name in self.pipes:
            warn(f"There is already a pipeline with the name {pipe_name}.")
            info(f"\t{self.pipes[pipe_name][INPUT]}", None)
            if self.yes_to_all:
                info("Yes flag is set.")
                overwrite = True
            elif self.no_to_all:
                attempt("No flag is set. Not overwriting pipeline.")
                return
            else:
                # ask the user
                overwrite = ask_yes_no(
                    f"Do you want to overwrite the pipeline {pipe_name}?"
                )
        if overwrite:
            attempt(f"Overwriting pipeline {pipe_name}.")

        new_pipe = self.create_pipeline_dict(pipe_name, pipe_string)
        self.pipes[pipe_name] = new_pipe
        self.update_pipes_json()

        if overwrite:
            success(f"{pipe_name} was updated in pipes.json")
        else:
            success(f"{pipe_name} was added to pipes.json")
            info(f"\t{self.pipes[pipe_name][INPUT]}", None)

        # if overwrite find pipes to update
        if overwrite:
            pipes_to_update = []
            for pipe, value in self.pipes.items():
                if pipe_name in value[SUBPIPELINES]:
                    pipes_to_update.append(pipe)
            if len(pipes_to_update) > 0:
                warn(
                    f"There are {len(pipes_to_update)} pipelines that use {pipe_name} as subpipeline."
                )
                self.yes_to_all = True  # FIXME ask the suer or find another way
                for pipe in pipes_to_update:
                    attempt(f"Updating {pipe}")
                    self.add_pipeline(f"{pipe}:{self.pipes[pipe][INPUT]}")

    def remove_subpipeline(self, pipe_name: str, subpipeline: str):
        """
        Removes a subpipeline from a pipeline.

        It reads in the parts of the pipeline string.
        Then it creates a new list of parts without the subpipeline.
        Then it creates a new pipeline dictionary with the new parts.
        Then it updates the pipes.json file.

        Parameters
        ----------
        pipe_name: str
            The name of the pipeline.
        subpipeline: str
            The name of the subpipeline.
        """
        input_string = self.pipes[pipe_name][INPUT]
        parts = re.split(r"(?<!:):(?!:)", input_string)[1:]
        new_parts = []
        for part in parts:
            if part == subpipeline:
                new_parts.extend(self.pipes[subpipeline][ELEMENTS])
            else:
                new_parts.append(part)
        pipe_string = ":".join(new_parts)
        tmp_pipe = self.create_pipeline_dict(pipe_name, pipe_string)
        self.pipe[pipe_name] = tmp_pipe
        self.update_pipes_json()
        success(f"{pipe_name} was updated in pipes.json")

    def delete_pipeline(self, pipe_name: str):
        """
        Deletes a pipeline from the pipes.json file.

        It will remove the pipeline from the pipes dictionary.
        Then it will update the pipes.json file.
        It checks if the pipe is used as a subpipeline in another pipeline.
        If so, it will ask the user if he wants to remove it or keep it.
        It might be usefull to keep it, if you are going to add it again.

        Parameters
        ----------
        pipe_name: str
            The name of the pipeline.
        """
        # Check if pipe with given name exist
        if pipe_name not in self.pipes:
            warn(f"There is no pipeline with the name {pipe_name}.")
            return
        # Check if pipe is used as subpipeline
        for pipe, value in self.pipes.items():
            if pipe_name in value[SUBPIPELINES]:
                warn(f"{pipe_name} is used as subpipeline in {pipe}.")
                info(f"\t{self.pipes[pipe][INPUT]}", None)
                if self.yes_to_all:
                    info("Yes flag is set.")
                    attempt("Removing subpipeline from pipeline.")
                    self.remove_subpipeline(pipe, pipe_name)
                elif self.no_to_all:
                    info("No flag is set.")
                    info(f"Keeping {pipe_name} as subpipeline in {pipe}.")
                else:
                    user_input = ask_yes_no(
                        f"Do you want to remove {pipe_name} as subpipeline from {pipe}?"
                    )
                    if user_input:
                        attempt("Removing subpipeline from pipeline.")
                        self.remove_subpipeline(pipe, pipe_name)

        # Delete pipe
        self.pipes.pop(pipe_name, None)  # None prevents KeyError
        self.update_pipes_json()
        success(f"{pipe_name} was removed from pipes.json")

    def change_subpipe_name(
        self, pipe_name: str, subpipe_old_name: str, subpipe_new_name: str
    ):
        """
        This function changes the name of a subpipeline in a pipeline.

        It changes the name in the subpipelines list.
        It changes the name in the input string.
        It updates the pipes.json file.

        Parameters
        ----------
        pipe_name: str
            The name of the pipeline.
        subpipe_old_name: str
            The old name of the subpipeline.
        subpipe_new_name: str
            The new name of the subpipeline.
        """
        # Change subpipeline entry
        tmp_subpipelines = self.pipes[pipe_name][SUBPIPELINES]
        tmp_subpipelines = list(
            map(
                lambda x: x.replace(subpipe_old_name, subpipe_new_name),
                tmp_subpipelines,
            )
        )
        self.pipes[pipe_name][SUBPIPELINES] = tmp_subpipelines
        # Change input string
        tmp_input = self.pipes[pipe_name][INPUT]
        parts = re.split(r"(?<!:):(?!:)", tmp_input)
        for idx, part in enumerate(parts):
            if part == subpipe_old_name:
                parts[idx] = subpipe_new_name
        tmp_input = ":".join(parts)
        self.pipes[pipe_name][INPUT] = tmp_input
        # Update pipes.json
        self.update_pipes_json()
        success(f"{subpipe_old_name} was changed to {subpipe_new_name} in {pipe_name}.")

    def rename_pipeline(self, old_name: str, new_name: str):
        """
        Renames a pipeline.

        It changes the name in the pipes dictionary.
        Then it updates the pipes.json file.
        It will also check if the pipeline is used as a subpipeline in
        another pipeline and change the name there as well.
        (if the user wants to)

        Parameters
        ----------
        old_name: str
            The old name of the pipeline.
        new_name: str
            The new name of the pipeline.
        """
        # Check if pipe with given name exist
        if old_name not in self.pipes:
            error(f"There is no pipeline with the name {old_name}.")
            exit()
        # Check if pipe with new name already exist
        if new_name in self.pipes:
            error(f"There is already a pipeline with the name {new_name}.")
            info(f"\t{self.pipes[new_name][INPUT]}", None)
            info("Rename the old pipeline first or delete it.")
            exit()
        # Check if pipe gets uses as subpipeline
        for pipe, value in self.pipes.items():
            if old_name in value[SUBPIPELINES]:
                warn(f"{old_name} is used as subpipeline in {pipe}.")
                info(f"\t{self.pipes[pipe][INPUT]}", None)
                if self.yes_to_all:
                    info("Yes flag is set.")
                    attempt("Changing subpipeline name in pipeline.")
                    self.change_subpipe_name(pipe, old_name, new_name)
                elif self.no_to_all:
                    info("No flag is set.")
                    info(f"Keeping {old_name} as subpipeline in {pipe}.")
                else:
                    user_input = ask_yes_no(
                        f"Do you want to change {old_name} to {new_name} as subpipeline in {pipe}?"
                    )
                    if user_input:
                        attempt("Changing subpipeline name in pipeline.")
                        self.change_subpipe_name(pipe, old_name, new_name)
        # Change name (delete old and inser new)
        tmp_pipe = self.pipes[old_name]
        tmp_input = tmp_pipe[INPUT]
        tmp_input = tmp_input.replace(old_name, new_name)
        tmp_pipe[INPUT] = tmp_input
        self.pipes.pop(old_name, None)  # None prevents KeyError
        self.pipes[new_name] = tmp_pipe
        # Save changes
        self.update_pipes_json()
        success(f"{old_name} was changed to {new_name}.")

    def list_pipelines(self, query: str = None):
        """
        Lists all pipelines.

        It prints the name of the pipeline and the input string.
        The output can be filtered with an optional filter.
        This will only show pipelines that contain the filter
        in their names or input strings.
        Filter: "___" means None (for now)

        Parameters
        ----------
        query: str
            The filter for the output.
        """
        if query == "___":
            query = None
        if query:
            attempt(f"Filter: {query}\n===================", None)
        else:
            attempt(f"All pipelines:\n===================", None)
        tmp_pipes = self.pipes
        for pipe, value in tmp_pipes.items():
            if (query and query in pipe) or not query:
                info(f"{pipe}:\n\t{value[INPUT]}", None)
            elif (query and query in value[INPUT]) or not query:
                info(f"{pipe}:\n\t{value[INPUT]}", None)

    def show_pipe_info(self, pipe_name: str):
        """
        Shows information about a pipeline.

        It prints the name of the pipeline, the input string and
        all subpipelines.

        Parameters
        ----------
        pipe_name: str
            The name of the pipeline.
        """
        if pipe_name not in self.pipes:
            error(f"There is no pipeline with the name {pipe_name}.")
            exit()
        attempt(f"Pipeline: {pipe_name}\n===================", None)
        info(f"Input:\n\t{self.pipes[pipe_name][INPUT]}", None)
        info(f"Subpipelines:\n\t{self.pipes[pipe_name][SUBPIPELINES]}", None)

    def create_output_file(self, pipe_string, output_file):
        """
        This function creates a bash script file.

        It contains all the commands that are needed to execute the pipeline.

        Parameters
        ----------
        pipe_string: str
            The pipeline string.
        output_file: str
            The name of the output file.
        """
        gstreamer_string = self.create_gstreamer_string(pipe_string)
        (
            gststreamer_string,
            pre_commands,
            post_commands,
        ) = self.prepare_command_execution(gstreamer_string)
        attempt(f"Creating output file: {output_file}")
        with open(output_file, "w") as file:
            for com in pre_commands:
                info(f"\t{com}", None)
                file.write(f"{com}\n")
            info(f"\t{gststreamer_string}", None)
            file.write(f"{gststreamer_string}\n")
            for com in post_commands:
                info(f"\t{com}", None)
                file.write(f"{com}\n")
        success(f"Output file created: {output_file}")

    def execute_commands(
        self, command: str, pre_commands: list = [], post_commands: list = []
    ):
        """
        This functions executes the commands to run a pipeline.

        It executes the pre_commands first, if there are any.
        Then it executes the pipeline/gstreamer command
        and waits for it to finish or the user to interrupt it.
        Finally it executes the post_commands, if there are any.

        Parameters
        ----------
        command: str
            The pipeline/gstreamer command.
        pre_commands: list
            A list of commands that should be executed before the pipeline.
        post_commands: list
            A list of commands that should be executed after the pipeline.
        """
        for pre_com in pre_commands:
            attempt(f"Executing pre command:\n\t {pre_com}")
            Popen(pre_com.split())

        attempt(f"Executing command:\n\t {command}")
        p = Popen(command.split())
        try:
            p.wait()
        except KeyboardInterrupt:
            try:
                p.terminate()
            except OSError:
                pass
            p.wait()

        for post_com in post_commands:
            attempt(f"Executing post command:\n\t {post_com}")
            Popen(post_com.split())

    def create_gstreamer_string(self, pipe_string: str) -> str:
        """
        This function creates a gstreamer string.

        It takes a pipeline string and creates a gstreamer string
        that can be executed by the gstreamer command line tool.
        It tries to find all variables of known pipelines or
        provided new variables with values.

        Parameters
        ----------
        pipe_string: str
            The pipeline string.

        Returns
        -------
        gstreamer_string: str
            The gstreamer string.
        """
        tux_pipes = []
        gstreamer_string = ""

        for element in re.split(r"(?<!:):(?!:)", pipe_string):
            input_variables = []
            element_variables = []

            # Check if variable input values are provided
            # (only works for know pipelines)
            if "(" in element:
                element, input_variables_string = element[:-1].split("(")
                input_variables = input_variables_string.split(";")
                # Check if lement is known pipe
                if element not in self.pipes.keys():
                    error(f"Variables provided for unknown pipe: {element}")
                    exit()
                element_tuxpipe = self.pipes[element][TUXPIPE]
                element_variables = self.pipes[element][VARIABLES]
            # no inputs provided
            else:
                if element in self.pipes.keys():
                    element_tuxpipe = self.pipes[element][TUXPIPE]
                    element_variables = self.pipes[element][VARIABLES]
                else:
                    element_tuxpipe = element

            # Separate values
            specific_values = {}
            unspecific_values = []
            for val in input_variables:
                if "#" in val:
                    specific_values[val.split("=")[0]] = val.split("=")[-1]
                else:
                    unspecific_values.append(val)

            # insert specifc values first
            for var, val in specific_values.items():
                if var in element_variables:
                    element_tuxpipe = element_tuxpipe.replace(
                        var + "=" + element_variables[var], val
                    )
                    # remove uses variable
                    element_variables.pop(var, None)

            # insert unspecific values
            for var, default_value in element_variables.items():
                current_value = ""
                replacement = f"{var}={default_value}"
                if len(unspecific_values) > 0:
                    current_value = unspecific_values.pop(0)
                if current_value != "":
                    element_tuxpipe = element_tuxpipe.replace(
                        replacement, current_value
                    )
                else:
                    element_tuxpipe = element_tuxpipe.replace(
                        replacement, default_value
                    )

            tux_pipes.append(element_tuxpipe)

        # combine tux pipes to one tuxpipe and create gstreamer pipeline
        tuxpipe = ":".join(tux_pipes)
        tmp_elements = re.split(r"(?<!:):(?!:)", tuxpipe)
        gstreamer_string = " ! ".join(tmp_elements)
        gstreamer_string = gstreamer_string.replace("  !", " !")
        gstreamer_string = gstreamer_string.replace(
            "gst-launch-1.0 ! ", "gst-launch-1.0 "
        )

        return gstreamer_string

    def prepare_command_execution(self, gstreamer_string: str) -> tuple:
        """
        This function prepares the command execution.

        It takes a gstreamer string and creates a list of commands
        that have to be executed before and after the gstreamer command.
        It also tries to do some basic checks on the commands.

        Parameters
        ----------
        gstreamer_string: str
            The gstreamer string.

        Returns
        -------
        pre_commands: list
            The list of pre commands.
        post_commands: list
            The list of post commands.
        """
        # Check for specific rules when using certain sinks, sources, elements
        # => Created needed pre and post commands
        pre_commands = []
        post_commands = []
        # kmssink
        if "kmssink" in gstreamer_string or "kmscube" in gstreamer_string:
            pre_commands.append("systemctl stop weston")
            post_commands.append("systemctl start weston")
            gstreamer_string = gstreamer_string.replace("kmssink", "kmssink can-scale=false")

        # FIXME this was added for the development on xilinx boards
        # Might need rework or removal
        if self.args.commands:
            print(self.args.commands)
            f = open(f"{self.args.commands}", "r")
            coms = json.load(f)
            pre_commands.extend(coms)
            f.close()

        return gstreamer_string, pre_commands, post_commands

    def run_input_string(self, input_string: str):
        """
        Directly runs a pipeline given as input.

        Parameters
        ----------
        input_string: str
            The input string.
        """
        gstreamer_string = self.create_gstreamer_string(input_string)
        gstreamer_string, pre_commands, post_commands = self.prepare_command_execution(
            gstreamer_string
        )  
        self.execute_commands(gstreamer_string, pre_commands, post_commands)

    def check_args(self):
        """
        Check the commandline arguments.

        First it checks if there is an input string if there are no arguments.
        Then it sets the flags.
        Then it runs through the possible options and arguments
        and calls the corresponding functions.
        """

        # check if there is an input string if there are no arguments
        if not self.args.input_string and not len(sys.argv) > 1:
            self.parser.print_help()
            exit()
        if self.args.input_string:
            self.input_string = self.args.input_string

        # flags
        # No > Yes
        if self.args.yes:
            self.yes_to_all = True
            self.no_to_all = False
        if self.args.no:
            self.no_to_all = True
            self.yes_to_all = False

        # options and arguments
        if self.args.add:
            if not self.args.input_string:
                error("No input_string/pipe given.")
                exit()
            self.add_pipeline(self.args.input_string)
        elif self.args.delete:
            self.delete_pipeline(self.args.delete[0])
        elif self.args.rename:
            self.rename_pipeline(self.args.rename[0], self.args.rename[1])
        elif self.args.list:
            self.list_pipelines(self.args.list)
        elif self.args.info:
            if not self.args.input_string:
                error("No input_string/pipe given.")
                exit()
            self.show_pipe_info(self.input_string)
        elif self.args.output:
            if not self.input_string:
                error("No input_string/pipe given.")
                exit()
            self.create_output_file(self.input_string, self.args.output)
        else:
            self.run_input_string(self.input_string)

        success("Done.")


# ==================== #
#         Main         #
# ==================== #
def main():
    """
    The main function.
    """
    header_message("TuxPipes")
    tp = TuxPipes()
    tp.check_args()


if __name__ == "__main__":
    main()
