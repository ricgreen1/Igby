# igby_lib.py for Igby UE Project Automator
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import os, json, time, random
from datetime import datetime
from inspect import stack

def clear_screen():

    os.system('cls' if os.name == 'nt' else 'clear')

def get_datetime():

    date_time = datetime.now()
    dt_string = date_time.strftime("%d/%m/%Y %H:%M:%S")

    return dt_string

def get_settings(settings_json_file = ''):

    #try to get settings file if one was not provided
    if settings_json_file == "":
        current_script_dir = get_current_script_dir()
        settings_dir = current_script_dir.replace('Python','')
        settings_json_file = r'{}ue_project_automator_settings.json'.format(settings_dir)

    # Opening JSON file
    with open(settings_json_file) as f:

        settings = json.load(f)

    return settings

def get_current_script_dir():

    current_script_dir = os.path.dirname(os.path.abspath(__file__))

    return current_script_dir


def get_module_settings(settings_from_json, module_sdefault_settings, logger):

    module_settings = {}
    missing_settings = []

    for module_default_setting in module_sdefault_settings:

        if module_default_setting[0] in settings_from_json:

            module_settings[module_default_setting[0]] = settings_from_json[module_default_setting[0]]
            del settings_from_json[module_default_setting[0]]

        elif len(module_default_setting) == 2:

            module_settings[module_default_setting[0]] = module_default_setting[1]

        else:

            missing_settings.append(module_default_setting[0])

    #assert for missing settings            
    if len(missing_settings):

        missing_settings_s = ""

        for missing_setting in missing_settings:

            missing_settings_s = "{}{}\n".format(missing_settings_s, missing_setting)

        raise(Exception("Missing mandatory settings:\n{}".format(missing_settings_s)))

    #report deprecated settings
    if len(settings_from_json):

        logger.log_ue("Warning! The following settings have been depricated and will be ignored.\n", "warning_clr")

        for deprecated_settings in settings_from_json:
            logger.log_ue(deprecated_settings, "warning_clr")

    return module_settings


#loger class
class logger:

    colors = {
    "normal_clr" : "\033[0;37;40m",
    "run_h_clr" : "\033[0;37;44m",
    "p4_h_clr" : "\033[0;37;105m",
    "module_h_clr" : "\033[0;37;100m",
    "success_h_clr" : "\033[0;37;42m",
    "failure_h_clr" : "\033[0;37;41m",
    "error_clr" : "\033[0;37;31m",
    "warning_clr" : "\033[0;37;33m",
    "info_clr" : "\033[0;37;94m"
    }


    def __init__(self, log_path=""):

        os.system('')

        self.valid_log_path = False
        self.prefix = ""

        if log_path != "":

            #for tracking ue startup progress widget
            self.startup = True
            self.progress_anim_frame = 0

            now = datetime.now()
            current_time = now.strftime("_%Y_%d_%m_%H_%M_%S")
            log_path = log_path.replace('.','{}.'.format(current_time))

            #create directory path if it doesn't exist
            dir_path = os.path.dirname(log_path)
            if not os.path.isdir(dir_path):
                os.makedirs(dir_path)

            f = open(log_path, "w")
            f.close()
            self.log_path = log_path
            self.valid_log_path = True


    def log(self, log_string, color_key = "normal_clr", print_to_console = True, print_to_log = True):
              
        if print_to_console:

            if log_string.endswith("\\r"):
                print(end='\x1b[2K')
                print("{}{}{} ".format(self.colors[color_key], log_string[0:-2], self.colors["normal_clr"]), end="\r")
            else:
                print("{}{}{} ".format(self.colors[color_key], log_string, self.colors["normal_clr"]))

        if print_to_log:

            if self.valid_log_path:

                with open(self.log_path, "a", encoding='utf8') as file:
                    file.write("\n{}".format(log_string))
            else:
                print()


    def log_ue(self, log_string, color_key = 'normal_clr'):

        log_string = "{}{}".format(self.prefix,log_string)
        log_string_igby = "IGBY_LOG_S>{}<IGBY_LOG_I{}<IGBY_LOG_E".format(color_key,log_string).replace("\n","<IGBY_LOG_E\nIGBY_LOG_S>{}<IGBY_LOG_I{}".format(color_key, self.prefix))
        print(log_string_igby)


    def log_filter_ue(self, log_string, debug = False):

        progress_anim_chars = '—\|/'

        if debug:

            self.log(log_string)
        
        else:

            if "IGBY_LOG_S>" in log_string:

                self.startup = False
                #log_string = log_string[0:len(log_string)-5]
                log_parts = log_string.split("IGBY_LOG_S>")
                color_key = log_parts[1].split("<IGBY_LOG_I")
                log_string = color_key[1].split("<IGBY_LOG_E")[0]
                log_message = log_string.replace("\\\\","\\")

                #handle errors
                if color_key[0] == "error_clr":
                    return log_message
                else:
                    self.log(log_message, color_key[0])
                    return False

            elif self.startup:

                print(f"{progress_anim_chars[int(self.progress_anim_frame % 4)]} {self.progress_anim_frame}", end="\r")
                self.progress_anim_frame += 1

    def add_characters(self, log_string, character, total_len):

        log_string_len = len(log_string.strip())
        len_to_add = total_len - log_string_len - 1

        for i in range(len_to_add):

            log_string = "{}{}".format(log_string, character)

        return log_string

    def reset_startup(self):

        self.startup = True
        self.progress_anim_frame = 0


#report class
class report:

    report_format = "csv"

    def __init__(self, report_save_dir, report_to_log, logger, module_name = ""):

        if report_save_dir == "" and not report_to_log:
            raise(Exception("Error! Report requires either REPORT_SAVE_DIR to conain a valid path or REPORT_TO_LOG to be True."))

        self.report_save_dir = report_save_dir
        self.report_to_log = report_to_log
        self.module_name = module_name
        self.logger = logger
        self.report = []
        self.report_s = ""

    def set_report_save_dir(self, report_save_dir):

        if report_save_dir == "":

            raise(Exception("Please provide a valid REPORT_SAVE_DIR setting."))
        
        else:

            if report_save_dir.endswith("\\"):
                self.report_save_dir = report_save_dir
            else:
                self.report_save_dir = f"{report_save_dir}\\"


    def add_row(self, row_list):

        self.report.append(row_list)


    def set_log_message(self, log_message):

        self.log_message = log_message


    def set_column_categories(self, column_categories):

        self.column_categories = column_categories


    def report_to_string(self, separator = ","):

        report = ""

        if self.column_categories != "":

            categories_s = ""

            for cat in self.column_categories:

                categories_s = f"{categories_s}{cat}{separator} "
            
            categories_s = categories_s[0:-2]
            report = f"{categories_s}\n"

        report_lines = []

        if len(self.report):

            for row_l in self.report:
                row_l = map(str, row_l)
                report_lines.append(separator.join(row_l))

        report_rows = "\n".join(report_lines)
        report = f"{categories_s}{report_rows}"

        return report


    def write_to_file(self, clear_after_write = True):

        if self.report_save_dir != "":

            #get module name if not set manually
            if self.module_name == "":
                module_name = os.path.basename(stack()[2][1]).split('.')[0]

            now = datetime.now()
            current_time = now.strftime("_%Y_%d_%m_%H_%M_%S")
            report_path = f"{self.report_save_dir}{module_name}/{module_name}{current_time}.{self.report_format}"

            #create directory path if it doesn't exist
            dir_path = os.path.dirname(report_path)
            if not os.path.isdir(dir_path):
                os.makedirs(dir_path)

            with open(report_path, "a", encoding='utf8') as file:
                file.write("{}".format(self.report_s))

            self.logger.log_ue(f"Saved report: {report_path}")

            if clear_after_write:
                self.report = ""


    def output_report(self, max_log = 0):

        self.report_s = self.report_to_string()

        if self.report_to_log:

            report_len = len(self.report)

            if report_len:

                self.logger.log_ue(self.log_message)

                if max_log > 0:

                    report_s_truncated = "\n".join(self.report_s.split("\n")[:max_log])
                    self.logger.log_ue(report_s_truncated)
                    self.logger.log_ue(f"\nReport tranucated. Displaying first {max_log} rows out of {report_len} total")
                    
                else:

                    self.logger.log_ue(self.report_s)

            else:

                self.logger.log_ue("Nothing to report.")

        self.write_to_file()

class long_process:

    done_char = ">"
    remaining_char = "-"
    
    def __init__(self, task_total, logger, bar_divisions = 100):

        self.bar_divisions = bar_divisions
        self.task_total = task_total
        self.progress = 0
        self.logger = logger
        self.previous_percent = -1

        pass

    def make_progress(self):

        self.progress += 1

        percent = int(self.progress / self.task_total * 100.0)

        if self.previous_percent < percent:

            progress_bar = ""

            for i in range(percent):

                progress_bar = f"{progress_bar}{self.done_char}"

            percent_string = f" {percent}% "
            progress_bar = f"{progress_bar}{percent_string}"

            for i in range((self.bar_divisions - percent - len(percent_string))):

                progress_bar = f"{progress_bar}{self.remaining_char}"

            self.logger.log_ue(f"{progress_bar}\r")

            self.previous_percent = percent

        if percent == 100:
            self.logger.log_ue(f"\r")


def encode_str(str_to_encode, seed):

    temp_dir = os.getenv('TEMP')
    random.seed(seed)
    file_name = int(random.random() * 1000000)
    file_path = f"{temp_dir}\\{file_name}.tmp"

    str_bit = str_to_bin(str_to_encode)
    seed_bit = str_to_bin(str(seed))

    encoded_str = ""
    bin_str = ""

    for i in range(len(str_bit)):

        value = (int(str_bit[i]) + int(seed_bit[i%len(seed_bit)]) + i % 2) % 2
        bin_str = f"{bin_str}{str(value)}"

    encoded_str = bin_to_str(bin_str)

    with open(file_path, 'w') as f:

        f.write(encoded_str)

def decode_str(seed):

    random.seed(seed)
    
    decoded_string = ""

    temp_dir = os.getenv('TEMP')
    file_name = int(random.random() * 1000000)
    file_path = f"{temp_dir}\\{file_name}.tmp"

    while not os.path.isfile(file_path):
        time.pause(0.01)

    with open(file_path, 'r') as f:

        line = f.read()

    os.remove(file_path)

    str_bit = str_to_bin(line)
    seed_bit = str_to_bin(str(seed))

    for i in range(len(str_bit)):

        value = (int(str_bit[i]) - int(seed_bit[i%len(seed_bit)])  - i % 2) % 2
        decoded_string = f"{decoded_string}{abs(value)}"

    decoded_string = bin_to_str(decoded_string)

    return decoded_string


def str_to_bin(str_to_encode):

    str_bin = ''.join(format(ord(i), '08b') for i in str_to_encode)
    return str_bin


def bin_to_str(bits_to_decode):
    
    string_out = ''

    for i in range(0, len(bits_to_decode), 8):
        temp_data = bits_to_decode[i:i + 8]
        decimal_data = int(temp_data, 2)
        string_out = string_out + chr(decimal_data)

    return str(string_out)

def dump_error(error):

    temp_dir = os.getenv('TEMP')
    pid = os.getpid()
    error_log_path = f"{temp_dir}\\igby_{pid}_error.txt"

    with open(error_log_path, "w") as f:
        f.write(error)
    
    return error_log_path