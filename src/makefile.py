from optparse import OptionParser
from os import listdir, environ
from os.path import dirname, expanduser, join, getmtime
from subprocess import call, Popen, PIPE
from sys import argv, platform

from shutil import rmtree

if platform == "win32":
    arduino_folder = "C:\Program Files (x86)\Arduino\\"
    temp_folder = expanduser("~\\AppData\\Local\\Temp\\")
    arduino_builder_folder = expanduser("~\\go_projects\\arduino-builder")
else:
    if 'ARDUINO_FOLDER' in environ.keys():
        arduino_folder = environ['ARDUINO_FOLDER']
    else:
        arduino_folder = expanduser("~/arduino-1.6.7/")
    arduino_builder_folder = expanduser("~/go_projects/arduino-builder")

teensyLC_build_vars = ["teensyLC.build.fcpu=48000000",
                       "teensyLC.build.flags.optimize=-Os",
                       "teensyLC.build.flags.ldspecs=--specs=nano.specs",
                       "teensyLC.build.keylayout=US_ENGLISH",
                       "teensyLC.build.usbtype=USB_SERIAL"]


def find_hexes():
    """
    Get only the most recent arduino compiled hex file.
    :return: the folder name
    :rtype: str
    """
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


def list_teensies():
    process = Popen(['tyc', 'list'], stdout=PIPE)
    out, err = process.communicate()
    out = out.decode("utf-8")
    devices = str(out).split('\r\n')
    parsed_devices = []
    for i in range(0, len(devices)):
        if len(devices[i]) > 0:
            devices[i] = devices[i].replace("add ", "")
            devices[i] = devices[i].replace("-Teensy Teensy", "")
            devices[i] = devices[i].replace(" LC", "")
            parsed_devices.append(devices[i])
    return parsed_devices


def format_folder(folder, path):
    return "\"" + join(folder, path).replace("\\", "\\\\") + "\""


def format_arduino_folder(path):
    return format_folder(arduino_folder, path)


def check_boards():
    boards = join(arduino_folder, "hardware/teensy/avr/boards.txt")
    fh = open(boards, "r")
    lines = fh.readlines()
    orig_num = len(lines)
    fh.close()
    for line in teensyLC_build_vars:
        found_line = False
        for inline in lines:
            if inline.find(line) >= 0:
                found_line = True
        if not found_line:
            lines.append(line)
    new_num = len(lines)
    if new_num > orig_num:
        fh = open(boards, "w")
        fh.writelines(lines)
        fh.close()


def compile(project_name="experiment_control"):
    # first, check the boards file for the build variables
    curr_dir = dirname(__file__)
    check_boards()
    command = [join(arduino_builder_folder, 'arduino-builder'),
               '-fqbn', 'teensy:avr:teensyLC',
               '-hardware', format_arduino_folder('hardware'),
               '-tools', format_arduino_folder('hardware/tools'),
               '-tools', format_arduino_folder('tools-builder'),
               '-libraries',
               format_arduino_folder('hardware/teensy/avr/libraries'),
               '-libraries', format_folder(join(curr_dir), project_name),
               format_folder(join(curr_dir, project_name), 'main.ino')]
    #command = [join(arduino_builder_folder, 'arduino-builder')]
    #print(' '.join(command))
    call(command)


def upload_latest(serial_number, hex_filename):
    command = ["tyc", "upload", "--board", serial_number, hex_filename]
    call(command)


def compile_upload(project_name="experiment_control",
                   exclude_list=['1743330'], clear=False, upload=True):
    if clear:
        last_hex = find_hexes()
        while last_hex is not None:
            rmtree(last_hex)
            last_hex = find_hexes()
    # get the devices, but remove the excluded devices
    devices = list_teensies()
    for exclude_device in exclude_list:
        if exclude_device in devices:
            devices.remove(exclude_device)
    if len(devices) == 0:
        raise IOError("Could not find teensy to program.")
    if len(devices) > 1:
        raise IOError("More than one teensy. Aborting.")
    compile(project_name=project_name)
    if upload:
        filename = join(find_hexes(), "main.ino.hex")
        upload_latest(serial_number=devices[0], hex_filename=filename)


def compile_upload_script():
    parser = CompileOption()
    (options, args) = parser.parse_args()
    options.exclude_list = options.exclude_list.split(",")
    compile_upload(options.project, exclude_list=options.exclude_list,
                   clear=options.clear, upload=options.upload)


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
        self.add_option("-e", "--exclude", action="store", dest="exclude_list",
                        default="", metavar='SERIAL_NUMBERS',
                        help="The serial numbers of teensies to exclude.")


if __name__ == "__main__":
    compile_upload()