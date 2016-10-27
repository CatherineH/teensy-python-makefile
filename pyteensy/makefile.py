from optparse import OptionParser
from os import listdir, environ, getcwd, walk
from os.path import dirname, expanduser, join, getmtime, basename
from subprocess import call, Popen, PIPE
from sys import argv, platform

from shutil import rmtree

from enum import Enum

if platform == "win32":
    arduino_folder = "C:\Program Files (x86)\Arduino\\"
    temp_folder = expanduser("~\\AppData\\Local\\Temp\\")
else:
    temp_folder = "/tmp"



class SourceTypes(Enum):
    unknown = 0
    python = 1
    arduino = 2


def format_folder(folder, path):
    return "\"" + join(folder, path).replace("\\", "\\\\") + "\""


def format_arduino_folder(path):
    return format_folder(arduino_folder, path)


teensy_build_vars = [".build.fcpu=48000000",
                     ".build.flags.optimize=-Os",
                     ".build.flags.ldspecs=--specs=nano.specs",
                     ".build.keylayout=US_ENGLISH",
                     ".build.usbtype=USB_SERIAL"]


class TeensyMake(object):
    def __init__(self, options=None):
        if options is not None:
            self.project = options.project
            self.project_name = options.project
            self.exclude_list = options.exclude_list
            self.clear = options.clear
            self.upload = options.upload
            self.device = options.device
            self._source_type = None
            self._teensy_list = None
            self._micropython_folder = None
            self._arduino_folder = None

    @property
    def source_type(self):
        if self._source_type is not None:
            return self._source_type
        files = listdir(self.project)
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
        return self._source_type

    def find_hexes(self):
        """
        Get only the most recent arduino compiled hex file.
        :return: the folder name
        :rtype: str
        """
        # TODO: skip finding in the temp_folder if source type is python
        if self.source_type == SourceTypes.arduino:
            most_recent = None
            for file in listdir(temp_folder):
                if file.find("arduino") == 0:
                    _filename = join(temp_folder, file)
                    if most_recent is None:
                        most_recent = _filename
                    else:
                        if getmtime(most_recent) < getmtime(_filename):
                            most_recent = _filename
            return most_recent
        elif self.source_type == SourceTypes.python:
            build_folder = join(self.arduino_folder, )

    @property
    def micropython_folder(self):
        if self._micropython_folder is not None:
            return self._micropython_folder
        if 'MICROPYTHON_FOLDER' in environ.keys():
            self._micropython_folder = environ['MICROPYTHON_FOLDER']
            return self._micropython_folder
        # if all else fails, search the computer
        for root, dirs, files in walk("/"):
            for name in dirs:
                if name.find("tools") >= 0 and root.endswith("micropython"):
                    self._micropython_folder = root
                    return self._micropython_folder

    @property
    def arduino_folder(self):
        if self._arduino_folder is not None:
            return self._arduino_folder
        if 'ARDUINO_FOLDER' in environ.keys():
            self._arduino_folder = environ['ARDUINO_FOLDER']
            return self._arduino_folder
        for root, dirs, files in walk("/"):
            for name in dirs:
                if name.find("tools") >= 0 and basename(root).startswith("arduino-"):
                    self._arduino_folder = root
                    return self._arduino_folder

    @property
    def teensy_list(self):
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
        boards = join(arduino_folder, "hardware/teensy/avr/boards.txt")
        fh = open(boards, "r")
        lines = fh.readlines()
        orig_num = len(lines)
        fh.close()
        build_lines = [self.device+build_opt for build_opt in teensy_build_vars]
        for line in build_lines:
            found_line = False
            for inline in lines:
                if inline.find(line) >= 0:
                    found_line = True
            if not found_line:
                lines.append(line+"\n")
        new_num = len(lines)
        if new_num > orig_num:
            fh = open(boards, "w")
            fh.writelines(lines)
            fh.close()

    def source_type(self):
        curr_dir = getcwd()
        _directory = join(curr_dir, self.project_name)
        _files = listdir(_directory)
        for _file in _files:
            if _file.endswith("main.py"):
                return SourceTypes.python
            elif _file.endswith("main.ino"):
                return SourceTypes.arduino
        return SourceTypes.unknown

    def compile_teensy(self):
        # first, check the boards file for the build variables
        curr_dir = getcwd()
        self.check_boards()
        parts = ['arduino-builder',
                   '-fqbn', 'teensy:avr:'+self.device,
                   '-hardware', format_arduino_folder('hardware'),
                   '-tools', format_arduino_folder('hardware/tools'),
                   '-tools', format_arduino_folder('tools-builder'),
                   '-libraries',
                   format_arduino_folder('hardware/teensy/avr/libraries'),
                   '-libraries', format_folder(join(curr_dir), self.project_name),
                   format_folder(join(curr_dir, self.project_name), 'main.ino')]
        command = ' '.join(parts)
        call(command, shell=True)

    def upload_latest(self):
        command = ["tyc", "upload", "--board", self.serial_number, self.hex_filename]
        call(command)

    def compile_upload(self):
        if self.clear:
            last_hex = self.find_hexes()
            while last_hex is not None:
                rmtree(last_hex)
                last_hex = self.find_hexes()
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
            self.hex_filename = join(self.find_hexes(), "main.ino.hex")
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