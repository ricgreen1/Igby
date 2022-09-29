# igby_lib.py for Igby UE Project Automator
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import os, json
from datetime import datetime

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


#log class
class logger:

    prefix = ""
    os.system('')
    startup = True
    progress_anim_frame = 0

    colors = {
    "normal_clr" : "\033[0;37;40m",
    "run_h_clr" : "\033[0;37;44m",
    "p4_h_clr" : "\033[0;37;105m",
    "module_h_clr" : "\033[0;37;100m",
    "success_h_clr" : "\033[0;37;42m",
    "failure_h_clr" : "\033[0;37;41m",
    "error_clr" : "\033[0;37;31m",
    "warning_clr" : "\033[0;37;33m"
    }


    def __init__(self, log_path=""):

        self.valid_log_path = False

        if log_path != "":
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

            print("{}{}{} ".format(self.colors[color_key], log_string, self.colors["normal_clr"]))

        if print_to_log:

            if self.valid_log_path:

                with open(self.log_path, "a", encoding='utf8') as file:
                    file.write("\n{}".format(log_string))
            else:
                print()


    def log_ue(self, log_string, color_key = 'normal_clr'):

        log_string = "{}{}".format(self.prefix,log_string)
        log_string_igby = "IGBY_LOG_S>{}<IGBY_LOG_E{}".format(color_key,log_string).replace("\n","\nIGBY_LOG_S>{}<IGBY_LOG_E".format(color_key))
        print(log_string_igby)


    def log_filter_ue(self, log_string, debug = False):

        progress_anim_chars = '—\|/'

        if "IGBY_LOG_S>" in log_string:

            self.startup = False
            log_string = log_string[0:len(log_string)-5]
            log_parts = log_string.split("IGBY_LOG_S>")
            log_parts = log_parts[-1].split("<IGBY_LOG_E")
            self.log(log_parts[1], log_parts[0])

        elif debug:

            self.log(log_string)

        elif self.startup:

            print("{}\r".format(progress_anim_chars[self.progress_anim_frame]), end="")
            self.progress_anim_frame = (self.progress_anim_frame + 1) % 4

    

    def add_characters(self, log_string, character, total_len):

        log_string_len = len(log_string.strip())
        len_to_add = total_len - log_string_len - 1

        for i in range(len_to_add):

            log_string = "{}{}".format(log_string, character)

        return log_string