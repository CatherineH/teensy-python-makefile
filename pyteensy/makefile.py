from optparse import OptionParser
from os import listdir, environ, getcwd, walk
from os.path import dirname, expanduser, join, getmtime, basename, isdir
from subprocess import call, Popen, PIPE
from sys import argv, platform

from shutil import rmtree

from enum import Enum

if platform == "win32":
    if "TEMP" in environ.keys():
        TEMP_FOLDER = environ["TEMP"]
    else:
        TEMP_FOLDER = expanduser("~\\AppData\\Local\\Temp\\")
else:
    TEMP_FOLDER = "/tmp"


class SourceTypes(Enum):
    unknown = 0
    python = 1
    arduino = 2


def format_folder(folder, path):
    """
    Escape the backslashes so that it can be used in a system call
    #TODO: replace this with some path stuff
    :param str folder: the dirname of the path
    :param str path: the basename of the path
    :return str: the formatted path
    """
    return "\"" + join(folder, path).replace("\\", "\\\\") + "\""

TEENSY_BUILD_VARS = [".build.fcpu=48000000",
                     ".build.flags.optimize=-Os",
                     ".build.flags.ldspecs=--specs=nano.specs",
                     ".build.keylayout=US_ENGLISH",
                     ".build.usbtype=USB_SERIAL"]


class TeensyMake(object):
    def __init__(self, options=None):
        if options is not None:
            self.project = options.project
            if self.project is None:
                raise ValueError("Please specify a project.")
            self.exclude_list = options.exclude_list
            self.clear = options.clear
            self.upload = options.upload
            self.device = options.device
            if self.device is None:
                self.device = "teensyLC"
            if self.device is "teensy32":
                self.device = "teensy31"
            self._source_type = None
            self._teensy_list = None
            self._micropython_folder = None
            self._arduino_folder = None
            self._project_directory = None

    @property
    def project_directory(self):
        """
        Get the full path to the project.
        :return str: the full path
        """
        if self._project_directory is not None:
            return self._project_directory
        else:
            curr_dir = getcwd()
            self._project_directory = join(curr_dir, self.project)
            return self._project_directory

    @property
    def source_type(self):
        """
        Identify the type of source in the project directory.
        :rtype: SourceTypes
        """
        if self._source_type is not None:
            return self._source_type

        files = listdir(self.project_directory)
        for file in files:
            # a python file must have either a main.py or a boot.py
            if file.find("main.py") == 0:
                self._source_type = SourceTypes.python
                return self._source_type
            if file.find("boot.py") == 0:
                self._source_type = SourceTypes.python
                return self._source_type
            if file.find("main.ino") == 0:
                self._source_type = SourceTypes.arduino
                return self._source_type
        self._source_type = SourceTypes.unknown
        if self._source_type == SourceTypes.unknown:
            raise ValueError("Source type not recognized.")

    def find_hex(self):
        """
        Get the most recently compiled hex file.
        :return str: the hex_filename
        """
        most_recent = None
        if self.source_type == SourceTypes.arduino:
            for file in listdir(TEMP_FOLDER):
                if file.find("arduino") == 0:
                    for _arduino_sketch_file in listdir(join(TEMP_FOLDER, file)):
                        _filename = join(TEMP_FOLDER, file, _arduino_sketch_file)
                        if _filename.endswith(".hex"):
                            if most_recent is None:
                                most_recent = _filename
                            else:
                                if getmtime(most_recent) < getmtime(_filename):
                                    most_recent = _filename
        elif self.source_type == SourceTypes.python:
            # at the moment, MicroPython only works with teensy 3.2
            build_folder = join(self.micropython_folder, "build")
            if not isdir(build_folder):
                return None
            hex_files = [_file for _file in listdir(build_folder) if _file.endswith(
                ".hex")]
            for hex_filename in hex_files:
                hex_filename = join(build_folder, hex_filename)
                if most_recent is None:
                    most_recent = hex_filename
                else:
                    if getmtime(most_recent) < getmtime(hex_filename):
                        most_recent = hex_filename
        return most_recent

    @property
    def micropython_folder(self):
        """
        Find the micropython folder. Grabbed either from the user's environment
        variables, or by looking for the folder micropython/tools.
        :return str: micropython foldername
        """
        if self._micropython_folder is not None:
            return self._micropython_folder
        if 'MICROPYTHON_FOLDER' in environ.keys():
            self._micropython_folder = environ['MICROPYTHON_FOLDER']
            return self._micropython_folder
        # if all else fails, search the computer
        for root, dirs, files in walk("/"):
            for name in dirs:
                if name.find("tools") >= 0 and root.endswith("micropython"):
                    self._micropython_folder = join(root, "teensy")
                    return self._micropython_folder

    @property
    def arduino_folder(self):
        """
        Find the arduino folder. Grabbed either from the user's environment
        variables, or by looking for the folder arduino-(ver num)/tools.
        :return str: arduino foldername
        """
        if self._arduino_folder is not None:
            return self._arduino_folder
        if 'ARDUINO_FOLDER' in environ.keys():
            self._arduino_folder = environ['ARDUINO_FOLDER']
            return self._arduino_folder
        for root, dirs, files in walk("/"):
            for name in dirs:
                if name.find("tools") >= 0 \
                        and (basename(root).startswith("arduino-")
                             or basename(root).startswith("Arduino")):
                    self._arduino_folder = root
                    return self._arduino_folder
        raise ValueError("Could not identify arduino folder!")

    @property
    def teensy_list(self):
        """
        Get the list of teensies currently plugged into the computer.
        :return list: list of teensy serial numbers
        """
        if self._teensy_list is None:
            parts = ['tyc', 'list']
            command = " ".join(parts)
            process = Popen(command, stdout=PIPE, shell=True)
            out, err = process.communicate()
            out = out.decode("utf-8")
            devices = str(out).split('\r\n')
            self._teensy_list = []
            for i in range(0, len(devices)):
                if len(devices[i]) > 0:
                    devices[i] = devices[i].split(" ")[1].split("-")[0]
                    self._teensy_list.append(devices[i])
        return self._teensy_list

    def check_boards(self):
        """
        Ensure that the build vars (cpu speed, keyboard, flags, usb type) are present
        in the arduino-builder boards config file.
        :return: None
        """
        boards = join(self.arduino_folder, "hardware/teensy/avr/boards.txt")

        fh = open(boards, "r")
        lines = fh.readlines()
        orig_num = len(lines)
        fh.close()
        build_lines = [self.device+build_opt for build_opt in TEENSY_BUILD_VARS]
        for line in build_lines:
            found_line = False
            for inline in lines:
                if inline.find(line) >= 0:
                    found_line = True
            if not found_line:
                lines.append(line + "\n")
        new_num = len(lines)
        if new_num > orig_num:
            fh = open(boards, "w")
            fh.writelines(lines)
            fh.close()

    def compile_teensy(self):
        # first, check the boards file for the build variables
        if self.source_type == SourceTypes.arduino:
            self.check_boards()
            parts = ['arduino-builder',
                       '-fqbn', 'teensy:avr:'+self.device,
                       '-hardware', format_folder(self.arduino_folder, 'hardware'),
                       '-tools', format_folder(self.arduino_folder,'hardware/tools'),
                       '-tools', format_folder(self.arduino_folder,'tools-builder'),
                       '-libraries',
                       format_folder(self.arduino_folder, 'hardware/teensy/avr/libraries'),
                       '-libraries', format_folder(self.project_directory, ""),
                       format_folder(self.project_directory, 'main.ino')]
        elif self.source_type == SourceTypes.python:
            parts = ["cd ", self.micropython_folder, "&&", "ARDUINO="+self.arduino_folder,
                     "FROZEN_DIR="+self.project_directory,
                     "make"]

        command = ' '.join(parts)
        try:
            call(command, shell=True)
        except Exception as e:
            print(command+" failed")

    def upload_latest(self):
        command = ["tyc", "upload", "--board", self.serial_number, self.hex_filename]
        call(command)

    def compile_upload(self):
        if self.clear:
            last_hex = self.find_hex()
            while last_hex is not None:
                rmtree(dirname(last_hex))
                last_hex = self.find_hex()
        if self.upload:
            # get the devices, but remove the excluded devices
            devices = self.teensy_list
            for exclude_device in self.exclude_list:
                if exclude_device in devices:
                    devices.remove(exclude_device)
            if len(devices) == 0:
                raise IOError("Could not find teensy to program.")
            if len(devices) > 1:
                raise IOError("More than one teensy. Aborting.")
        self.compile_teensy()
        if self.upload:
            self.hex_filename = self.find_hex()
            self.serial_number = devices[0]
            self.upload_latest()


def compile_upload_script():
    parser = CompileOption()
    (options, args) = parser.parse_args()
    options.exclude_list = options.exclude_list.split(",")
    _make = TeensyMake(options)
    _make.compile_upload()


class CompileOption(OptionParser):
    def __init__(self):
        OptionParser.__init__(self)
        self.add_option("-u", "--upload", action="store_true", dest="upload",
                        default=False, metavar='OPTION',
                        help="If the tag is present, upload the compiled "
                             "hex to the first teensy found.")
        self.add_option("-c", "--clear", action="store_true", dest="clear",
                        default=False, metavar='OPTION',
                        help="If the tag is present, any existing generated "
                             "files will be cleared.")
        self.add_option("-p", "--project", action="store", dest="project",
                        default=None, metavar='FOLDERNAME',
                        help="The foldername of the project. By default, "
                             "the project entrypoint is a file called "
                             "main.ino in the projectname folder.")
        self.add_option("-d", "--device", action="store", dest="device",
                        default=None, metavar='DEVICE',
                        help="The teensy device name, i.e., teensyLC or "
                             "teensy31.")
        self.add_option("-e", "--exclude", action="store", dest="exclude_list",
                        default="", metavar='SERIAL_NUMBERS',
                        help="The serial numbers of teensies to exclude.")


if __name__ == "__main__":
    _make = TeensyMake()
    _make.compile_upload()