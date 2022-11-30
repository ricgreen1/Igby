
# igby.py Igby UE Project Automator
# Developed by Richard Greenspan | igby.rg@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

__version__ = "0.2.0"

import igby_lib, sys, time, subprocess, perforce_helper, os, importlib, traceback

current_script_dir = igby_lib.get_current_script_dir()

def run(settings_json_file, debug = False):
    os.system('cls')
    os.system('title Igby')
    settings = igby_lib.get_settings(settings_json_file)
    run_count = 0
    max_runs = settings["MAX_RUNS"]
    min_wait_sec = settings["MIN_WAIT_SEC"]
    ue_cmd_exe_path = settings["UE_CMD_EXE_PATH"]
    ue_project_path = settings["UE_PROJECT_PATH"]

    #init logger
    logger = igby_lib.logger(settings["LOG_PATH"])
    
    #output location of settings file and containing settings for reference
    logger.log("Settings File Path: {}".format(settings_json_file))

    with open(settings_json_file, "r") as file:

        for line in file:
            logger.log(line.replace("\n",""))

    #start main loop
    while True:

        logger.reset_startup()

        success = True

        run_start_time = int(time.time())
        run_count+=1
        date_time = igby_lib.get_datetime()

        logger.log("")
        logger.log("")
        logger.log("")
        header_str = "                               Igby v{} - Run #{} {}                               ".format(__version__, run_count, date_time)
        header_str_len = len(header_str)
        logger.log(header_str,'run_h_clr')
        logger.log("")

        #run the PRE_RUN_COMMAND from settings. This is a good place to get/build latest engine.
        pre_run_python_command = settings["PRE_RUN_PYTHON_COMMAND"]

        pre_run_update = False

        if pre_run_python_command != "":
            logger.log("Running Pre Run Python Command: {}".format(pre_run_python_command))
            exec("import {}".format(pre_run_python_command.split('.')[0]))
            pre_run_command_result = eval(pre_run_python_command)

            # Pre Run Command result should be an array with 3 elements. 
            # Element 1 is a bool which dictates if pre_run_python_command execution was successful and process should continue.
            # Element 2 is a bool which dictates whether there was an update which should result in execution of modules.
            # Element 3 is a string with info that you may want to output to log.
            if(pre_run_command_result[1]):
                logger.log("Pre Run Command resulted in the following update which will trigger module execution for this run.")

            logger.log(pre_run_command_result[2])

            if not pre_run_command_result[0]:
                return False

        logger.log("")
        logger.log(logger.add_characters(" Perforce Syncing. Please don't interrupt the process!", " ", header_str_len), "p4_h_clr")
        logger.log("")

        #init perforce
        if 'p4' not in locals():
            logger.log("Initializing Perforce.")
            logger.log("")
            p4 = perforce_helper.p4_helper(settings["P4_PORT"], settings["P4_USER"], settings["P4_CLIENT"], "")

        #test p4 connection
        if not p4.connected:
            logger.log("Perforce connection could not be established! Will try again during next run.", "error_clr")
            logger.log("")
            success = False
        else:
            #Sync to latest
            changes = False
            p4_dirs_to_sync = settings["P4_DIRS_TO_SYNC"]

            for p4_dir_to_sync in p4_dirs_to_sync:

                logger.log("\t{}".format(p4_dir_to_sync))
                results = p4.get_latest(p4_dir_to_sync)

                if results == []:
                    logger.log("\t\tNo Changes")
                else:
                    changes = True
                    logger.log("\t\tSynced")
                    for cl in results:
                        logger.log("\t\tHead CL: {} File Count: {} Total Size: {}".format(cl["change"], cl["totalFileCount"], cl["totalFileSize"]))

            logger.log("")
            logger.log(logger.add_characters(" Perforce Syncing Completed.", " ", header_str_len),"p4_h_clr")

            #Only run if there were changes to sync or pre run
            if changes or pre_run_update or settings["FORCE_RUN"]:

                #Check for assets that are not in perforce
                if settings["PROJECT_CONTENT_INTEGRITY_TEST"]:
                    
                    logger.log("Testing project content integrity.\n")
                    project_integrity_report = ""
                    abs_content_path = f"{os.path.dirname(ue_project_path)}\\Content"
                    p4_have_content_files = set(p4.get_have_files_in_folder(abs_content_path))
                    local_content_files = set()
                    
                    for r, d, f in os.walk(abs_content_path):
                        for file in f:
                            local_content_files.add(os.path.join(r, file).replace("\\","/"))

                    local_files_not_in_depot = list(local_content_files - p4_have_content_files)

                    if len(local_files_not_in_depot):
                        
                        files = " NID\n".join(local_files_not_in_depot)
                        project_integrity_report = f"The following project files are present locally but are not in the depot:\n\n{files}"

                    depot_files_not_in_local = list(p4_have_content_files - local_content_files)

                    if len(depot_files_not_in_local):

                        files = " NIL\n".join(depot_files_not_in_local)
                        project_integrity_report = f"{project_integrity_report}\nThe following project files are in depot but are not present locally.\n\n{files}"

                    if len(local_files_not_in_depot) or len(depot_files_not_in_local):

                        error_log_path = igby_lib.dump_error(project_integrity_report)
                        logger.log("Halting igby run due to project content inconsistencies.\nDetailed information can be found in in this report: {}".format(error_log_path), "error_clr")
                        return False
                    else:
                        logger.log("Project content integrity confirmed.")
            
                #launch headless UE and run command
                settings_json_file_ds = settings_json_file.replace('\\','/')

                cmd = '"{}" "{}" SILENT -stdout -FullStdOutLogOutput -run=pythonscript -script="import igby; igby.run_modules(\'{}\',\'{}\',{})"'.format(ue_cmd_exe_path, ue_project_path, settings_json_file_ds, p4.p4.password, header_str_len)

                if debug:
                    logger.log("cmd = {}".format(cmd))
                try:
                    #setup pythonpath env var and run cmd
                    my_env = os.environ.copy()
                    python_dir = current_script_dir
                    automation_modules_dir = "{}\\Igby_Modules".format(python_dir)

                    if("UE4Editor-Cmd.exe" in ue_cmd_exe_path):
                        my_env["PYTHONPATH"] = "{};{}".format(python_dir, automation_modules_dir)
                    elif("UnrealEditor-Cmd.exe" in ue_cmd_exe_path):
                        my_env["UE_PYTHONPATH"] = "{};{}".format(python_dir, automation_modules_dir)

                    process = subprocess.Popen(cmd, env=my_env, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

                    logger.log("\nLaunching Headless Editor: {}".format(ue_cmd_exe_path))
                    logger.log("Loading Project: {}".format(ue_project_path))
                    logger.log("Loading a large project may take some time. Please be patient! :)\n")

                    ue_error_message = ""
                    error_detected = False

                    while process.poll() is None:
                        stdout_line = str(process.stdout.readline())
                        error = logger.log_filter_ue(stdout_line, debug)

                        if error: #collect full error.
                            ue_error_message = f"{ue_error_message}\n{error}"
                            error_detected = True
                        elif error_detected:
                            raise Exception(ue_error_message)

                    process.stdout.close()

                except Exception:

                    error_message = traceback.format_exc()

                    logger.log("ERROR During Unreal Engine Execution :(", "error_clr")
                    error_message = traceback.format_exc()
                    logger.log(error_message, "error_clr")

                    if settings["HALT_ON_ERROR"]:
                        logger.log("Igby execution halted due to error.")
                        return False
                    else:
                        logger.log("Trying again.")
                        success = False
            else:
                logger.log("Skipping Run Because No Changes.")

        logger.log("\n")

        elapsed_time = int(time.time()) - run_start_time


        if success:
            logger.log("Run #{} Completed In {} sec.\n".format(run_count, elapsed_time))

        #evaluate max runs
        if max_runs > 0 and run_count == max_runs:
            logger.log("Reached Max Run Limit: {}".format(max_runs))
            break

        #wait between runs if necessary
        while elapsed_time < min_wait_sec:
            print("Waiting for {} seconds: {}\r".format(min_wait_sec,elapsed_time), end="")
            elapsed_time+=1
            time.sleep(1)
        else:
            print("                               ")

        

def run_modules(settings_json_file, p4_password, header_str_len):

    success = True

    try:

        import inspect, unreal, igby_lib, ue_asset_lib

        settings = igby_lib.get_settings(settings_json_file)

        logger = igby_lib.logger()

        p4 = perforce_helper.p4_helper(settings["P4_PORT"], settings["P4_USER"], settings["P4_CLIENT"], p4_password, settings["P4_CL_DESCRIPTION_PREFIX"])

        if not p4.connect():
            logger.log_ue("Could not connect to perforce! Exiting.")
            success = False
            return success

        modules_to_run = settings["MODULES_TO_RUN"]

        #wait for assets to be loaded for ue4
        asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()

        if unreal.SystemLibrary.get_engine_version().startswith('4.2'):
            asset_registry.wait_for_completion()

        #Run modules
        for module_dict in modules_to_run:

            #introduce module default settings
            module_name = list(module_dict.keys())[0]

            if "MODULE_DEFAULT_SETTINGS" in settings:

                for module_default_setting in settings["MODULE_DEFAULT_SETTINGS"]:

                    if module_default_setting not in module_dict[module_name]:

                        module_dict[module_name][module_default_setting] = settings["MODULE_DEFAULT_SETTINGS"][module_default_setting]

            module_success = True

            try:

                logger.log_ue("\n")
                logger.log_ue(logger.add_characters(" [ {} ]".format(module_name), " ", header_str_len), "module_h_clr")
                logger.log_ue("\n")

                module = importlib.import_module(module_name)
                module_run = getattr(module, 'run')
                module_start_time = int(time.time())

                arg_spec = inspect.getargspec(module_run)

                logger.prefix = "    "
                
                if "p4" in arg_spec[0]:
                    module_run(module_dict[module_name], logger, p4)
                else:
                    module_run(module_dict[module_name], logger)

                logger.prefix = ""

                elapsed_time = int(time.time()) - module_start_time

            except Exception:

                module_success = False
                error_message = traceback.format_exc()
                logger.log_ue(error_message, "error_clr")

            if module_success:
                logger.log_ue("\n [ {}s ] ".format(elapsed_time), "success_h_clr")
            else:
                logger.log_ue("\n [ {}s ] {} Failed ".format(elapsed_time, module_name), "failure_h_clr")
    
    except Exception:

        success = False
        error_message = traceback.format_exc()
        logger.log_ue(error_message, "error_clr")

    return success


def get_igby_sesttings_info():

    st = "type"
    sd = "default"
    si = "info"
    false = False
    true = True

    igby_settings_info = {
    "LOG_PATH":{st:str, sd:"", si:"Path where igby will save the log. The resulting path will be modified to include a timestamp in the filename."},
    "PRE_RUN_PYTHON_COMMAND":{st:str, sd:"sample_pre_run_command.run()", si:"Python command that igby will run before launching UE module execution."},
    "MIN_WAIT_SEC":{st:int, sd:"60", si:"Minimum number of seconds igby should wait before next run"},
    "MAX_RUNS":{st:int, sd:0, si:"Number of runs igby will complete. 0 = Unlimited"},
    "P4_PORT":{st:str, si:"Perforce server address and port. ex: 111.222.333.444:1666"},
    "P4_USER":{st:str, si:"Perforce user name."},
    "P4_CLIENT":{st:str, si:"Perforce client spec name."},
    "P4_CL_DESCRIPTION_PREFIX":{st:str, sd:"#igby_automation", si:"Perforce changelist description prefix. ex: #igby_automation"},
    "P4_DIRS_TO_SYNC":{st:list(str), si:"List of directories and files to sync at the beginning of each run."},
    "UE_CMD_EXE_PATH":{st:str, si:"Path to the Unreal Command executable. ex: D:\\Epic Games\\UE_5.1\\Engine\\Binaries\\Win64\\UnrealEditor-Cmd.exe"},
    "UE_PROJECT_PATH":{st:str, si:"Project path. ex: D:\\Unreal Projects\\LyraStarterGame\\Lyra.uproject"},
    "PROJECT_CONTENT_INTEGRITY_TEST":{st:bool, sd:true, si:"Test to see if project content matches files in perforce depot"},
    "HALT_ON_ERROR":{st:bool, sd:true, si:"Determines if Igby should halt execution on error."},
    "FORCE_RUN":{st:bool, sd:false, si:"Determines if Igby should run even if there aren't any updates established at the beginnign of execution."},
    }

    return igby_settings_info



if __name__ == "__main__":

    debug_flag = False

    if len(sys.argv) == 3 and sys.argv[2] == "-d":
        debug_flag = True

    run(sys.argv[1], debug=debug_flag)