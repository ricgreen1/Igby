# igby_lib.py for Igby UE Project Automator
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import os, json, hashlib
from datetime import datetime
from inspect import stack

def clear_screen():

    os.system('cls' if os.name == 'nt' else 'clear')

def get_datetime():

    date_time = datetime.now()
    dt_string = date_time.strftime("%m/%d/%Y %H:%M:%S")

    return dt_string


def get_current_script_dir():

    current_script_dir = os.path.dirname(os.path.abspath(__file__))

    return current_script_dir


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


def validate_settings(settings_from_json, settings_definition, logger):

    script_name = os.path.basename(stack()[1][1]).split('.')[0]
    function_name = stack()[1][3]
    try:
        class_name = stack()[1][0].f_locals['self'].__class__.__name__
    except:
        class_name = None

    if class_name:
        caller = f"{class_name}.{function_name}"
    else:
        caller = f"{function_name}"


    validation_message = (f"Validating settings for: {script_name}.{caller}")
    warnings = []
    errors = []

    validated_settings = {}

    validated_setting_keys = set(settings_from_json.keys()).intersection(set(settings_definition.keys()))
    missing_setting_keys = set(settings_definition.keys()) - set(settings_from_json.keys())
    
    for key in validated_setting_keys:
        if "deprecated" in settings_definition[key]:
            warnings.append(f"Warning! Deprecated setting: {key} - {validated_setting_keys[key]['deprecated']}")
        else:
            validated_settings[key] = settings_from_json[key]

    missing_required = []
    missing_defaults = []

    for missing_setting in missing_setting_keys:


        if "default" in settings_definition[missing_setting]:
            validated_settings[missing_setting] = settings_definition[missing_setting]["default"]
            if "optional" not in settings_definition[missing_setting]:
                missing_defaults.append(f"{missing_setting}:{validated_settings[missing_setting]}")
        elif "optional" in settings_definition[missing_setting]:
            continue
        elif not "deprecated" in settings_definition[missing_setting]:
            missing_required.append(f"{missing_setting}: type={settings_definition[missing_setting]['type']} ({settings_definition[missing_setting]['info']})")

    if len(missing_defaults):

        for missing_default in missing_defaults:
            warnings.append(f"\nWarning! Default used due to missing setting: {missing_default}")

    if len(missing_required):

        for missing_setting in missing_required:
            errors.append(f"\nError! Igby can't run without this setting: {missing_setting}")

    if len(errors) or len(warnings):
        logger.log(validation_message)

        for warning in warnings:
            logger.log(warning, "warning_clr")

        for error in errors:
            logger.log(error, "error_clr")
        
        if len(errors):
            raise Exception("Missing settings required for igby to run.")

    return validated_settings

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

    logger_settings_defenition = {
    "LOG_PATH":{"type":"str", "info":"File path where the log will be saved."}
    }

    def __init__(self, log_path=""):

        #check if initiated inside unreal.
        try:
            import unreal
            self.in_ue = True
        except:
            self.in_ue = False
        pass

        os.system('')

        self.prefix = ""

        self.open_file = None

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

            self.open_file = open(log_path, "w")
            self.log_path = log_path

    def __del__(self):

        if self.open_file:
            self.open_file.close()


    def log(self, log_string, color_key = "normal_clr", print_to_console = True, print_to_log = True):

        #support log function when in ue by redirecting to log_ue.
        if self.in_ue:
            self.log_ue(log_string, color_key, print_to_console, print_to_log)
            return
              
        if print_to_console:

            if log_string.endswith("\\r"):
                print(end='\x1b[2K')
                print("{}{}{} ".format(self.colors[color_key], log_string[0:-2], self.colors["normal_clr"]), end="\r")
            else:
                print("{}{}{} ".format(self.colors[color_key], log_string, self.colors["normal_clr"]))

        if print_to_log:

            if self.open_file:
                self.open_file.write("\n{}".format(log_string))
                self.open_file.flush()


    def log_ue(self, log_string, color_key = 'normal_clr', print_to_console = True, print_to_log = True):

        log_string = "{}{}".format(self.prefix,log_string)
        log_string_igby = f"IGBY_LOG_S>{color_key},{str(print_to_console)},{str(print_to_log)}<IGBY_LOG_I{log_string}<IGBY_LOG_E".replace("\n",f"<IGBY_LOG_E\nIGBY_LOG_S>{color_key},{str(print_to_console)},{str(print_to_log)}<IGBY_LOG_I{self.prefix}")
        print(log_string_igby)


    def log_filter_ue(self, log_string, debug = False):

        progress_anim_chars = '—\|/'

        if debug:

            self.log(log_string)
        
        else:

            if "IGBY_LOG_S>" in log_string:

                self.startup = False
                #log_string = log_string[0:len(log_string)-5]
                log_parts = log_string.split("IGBY_LOG_S>")[1].split("<IGBY_LOG_I")
                log_args = log_parts[0].split(",")
                color_key = log_args[0]
                print_to_console = log_args[1] == "True"
                print_to_log = log_args[2] == "True"
                log_string = log_parts[1].split("<IGBY_LOG_E")[0]
                log_message = log_string.replace("\\\\","\\")

                #handle errors
                if color_key == "error_clr":
                    return log_message
                else:
                    self.log(log_message, color_key, print_to_console, print_to_log)
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

    report_settings_defenition = {
    "REPORT_SAVE_DIR":{"type":"str", "info":"Directory where the report will be saved."}, 
    "REPORT_TO_LOG":{"type":"bool", "default":False, "info":"Determines if the report will be presented in the log."},
    "REPORT_LINE_LIMIT":{"type":"int", "optional":True, "default":0, "info":"Max number of lines to present in report."},
    "REPORT_ONLY_SAVE_UNIQUE":{"type":"bool", "default":False, "info":"Determines if only unique reports will be saved."},
    "REPORT_MODULE_NAME":{"type":"str", "optional":True, "default":"", "info":"Optional module name."},
    "REPORT_FILE_NAME_POSTFIX":{"type":"string", "optional":True, "default":"", "info":"Optional string to add to the end of the report file name."},
    "REPORT_FILE_NAME_PREFIX":{"type":"string", "optional":True, "default":"", "info":"Optional string to add to the beginning of the report file name."},
    "REPORT_SUBDIR":{"type":"string", "optional":True, "default":"", "info":"Optional subdirectory for report path."}
    }

    def __init__(self, settings, logger):

        validated_settings = validate_settings(settings, self.report_settings_defenition, logger)
        
        self.report_save_dir = validated_settings["REPORT_SAVE_DIR"]
        self.report_to_log = validated_settings["REPORT_TO_LOG"]
        self.only_save_unique_reports = validated_settings["REPORT_ONLY_SAVE_UNIQUE"]
        self.module_name = validated_settings["REPORT_MODULE_NAME"]
        self.file_name_postfix = validated_settings["REPORT_FILE_NAME_POSTFIX"]
        self.file_name_prefix = validated_settings["REPORT_FILE_NAME_PREFIX"]
        self.report_subdir = validated_settings["REPORT_SUBDIR"]
        self.report_line_limit = validated_settings["REPORT_LINE_LIMIT"]
        self.logger = logger
        self.report = []
        self.report_s = ""
        self.column_categories = []
        self.report_header = ""
        

    def set_report_save_dir(self, report_save_dir):

        if report_save_dir == "":

            raise(Exception("Please provide a valid REPORT_SAVE_DIR setting."))
        
        else:

            if report_save_dir.endswith("\\"):
                self.report_save_dir = report_save_dir
            else:
                self.report_save_dir = f"{report_save_dir}\\"
            

    def set_report_file_name_prefix(self, file_name_prefix):
            
        if file_name_prefix == "":

            raise(Exception("Please provide a valid file_name_prefix setting."))
        
        else:

            self.file_name_prefix = file_name_prefix


    def add_row(self, row_list):

        self.report.append(row_list)


    def set_log_message(self, log_message):

        self.log_message = log_message


    def set_column_categories(self, column_categories):

        self.column_categories = column_categories


    def set_report_header(self, header):

        self.report_header = header


    def set_report_subdir(self, report_subdir):

        self.report_subdir = report_subdir


    def report_to_string(self, separator = ","):
            
        report = ""

        if self.report_header != "":

            report = f"{report}{self.report_header}\n"

        if len(self.column_categories):

            categories_s = ""

            for cat in self.column_categories:

                categories_s = f"{categories_s}{cat}{separator} "
            
            categories_s = categories_s[0:-2]
            report = f"{report}{categories_s}\n"

        report_lines = []

        line_count = 0

        if len(self.report):

            for row_l in self.report:

                row_l = map(str, row_l)
                report_lines.append(separator.join(row_l))

                line_count+=1

                if self.report_line_limit > 0 and line_count == self.report_line_limit:
                    break
 
        report_rows = "\n".join(report_lines)
        report = f"{report}{report_rows}\n"

        return report


    def write_to_file(self, clear_after_write = True):

        if self.report_save_dir != "":

            #get module name if not set manually
            if self.module_name == "":
                module_name = os.path.basename(stack()[2][1]).split('.')[0]
            else:
                module_name = self.module_name

            self.report_dir = f"{self.report_save_dir}{module_name}\\"
            
            if self.report_subdir != "":
                self.report_dir = f"{self.report_dir}{self.report_subdir}\\"

            #only write report if it's qunique
            write_report = True

            if self.only_save_unique_reports and os.path.isdir(self.report_dir):
               
                max_ctime = 0
                for file in os.listdir(self.report_dir):
                    file_path = f"{self.report_dir}{file}"
                    cur_ctime = os.path.getctime(file_path)
                    if cur_ctime > max_ctime:
                        latest_file = file_path
                        max_ctime = cur_ctime
            
                if max_ctime > 0:
                    with open(latest_file, mode="r", encoding="utf-8") as f:
                      
                        last_report_content = f.read()
                        last_report_content_h = hashlib.md5(last_report_content.encode()).hexdigest()
                        current_report_content_h = hashlib.md5(self.report_s.encode()).hexdigest()

                        if last_report_content_h == current_report_content_h:
                            self.logger.log_ue(f"Identical to last report: {latest_file}")
                            write_report = False

            if write_report:
                now = datetime.now()
                current_time = now.strftime("_%Y_%m_%d_%H_%M_%S")
                self.report_path = f"{self.report_dir}{self.file_name_prefix}_{module_name}{current_time}{self.file_name_postfix}.{self.report_format}"

                #create directory path if it doesn't exist
                dir_path = os.path.dirname(self.report_path)
                if not os.path.isdir(dir_path):
                    os.makedirs(dir_path)

                with open(self.report_path, "w", encoding='utf-8') as file:
                    file.write(self.report_s)

                self.logger.log_ue(f"Saved report: {self.report_path}")

            if clear_after_write:
                self.report = []


    def output_report(self):

        self.report_s = self.report_to_string()
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

            self.logger.log(f"{progress_bar}\r", "normal_clr", True, False)

            self.previous_percent = percent

        if percent == 100:
            self.logger.log("\r", "normal_clr", True, False)


def dump_error(error):

    temp_dir = os.getenv('TEMP')
    pid = os.getpid()
    error_log_path = f"{temp_dir}\\igby_{pid}_error.txt"

    with open(error_log_path, "w") as f:
        f.write(error)
    
    return error_log_path


def get_lib_dir():

    script_dir = f"{get_current_script_dir()}/Lib"
    return script_dir