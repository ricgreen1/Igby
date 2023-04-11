# igby.py Igby UE Project Automator
# Developed by Richard Greenspan | igby.rg@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

__version__ = "1.1.0"

import igby_lib, perforce_helper, ugs_lib, prerequisites_lib, sys, time, subprocess, os, importlib, traceback

def run(settings_json_file, debug = False):

    igby_settings_definition = {
    "LOG_PATH":{"type":"str", "info":"Path where igby will save the log. The resulting path will be modified to include a timestamp in the filename."},
    "PRE_RUN_PYTHON_COMMAND":{"type":"str", "optional":True, "default":"sample_pre_run_command.run()", "info":"Python command that igby will run before launching UE module execution."},
    "MIN_WAIT_SEC":{"type":"int", "default":60, "info":"Minimum number of seconds igby should wait before next run"},
    "MAX_RUNS":{"type":"int", "default":0, "info":"Number of runs igby will complete. 0 = Unlimited"},
    "P4_DIRS_TO_SYNC":{"type":"list(str)", "info":"List of directories and files to sync at the beginning of each run."},
    "UE_CMD_EXE_PATH":{"type":"str", "info":"Path to the Unreal Command executable. ex: D:\\Epic Games\\UE_5.1\\Engine\\Binaries\\Win64\\UnrealEditor-Cmd.exe"},
    "UE_PROJECT_PATH":{"type":"str", "info":"Project path. ex: D:\\Unreal Projects\\LyraStarterGame\\Lyra.uproject"},
    "UGS_EXE_PATH":{"type":"str", "optional":True, "info":"Ugs executable path. ex: C:\\Users\\user\\AppData\\Local\\UnrealGameSync\\Latest\\ugs.exe"},
    "PROJECT_CONTENT_INTEGRITY_TEST":{"type":"bool", "default":True, "info":"Test to see if project content matches files in perforce depot"},
    "HALT_ON_ERROR":{"type":"bool", "default":True, "info":"Determines if Igby should halt execution on error."},
    "FORCE_RUN":{"type":"bool", "default":False, "info":"Determines if Igby should run even if there aren't any updates established at the beginnign of execution."},
    "MODULE_SETTING_PRESETS":{"type":"dict", "info":"This is where you can define presets for module settings."},
    "MODULES_TO_RUN":{"type":"list(dict)", "info":"This is a dictionary of all modules and their settings"},
    "MODULE_DEFAULT_SETTINGS":{"deprecated":"Replaced by \"MODULE_SETTING_PRESETS\" in order to support multiple presets."},
    "PY_LIBS":{"type":"dict(dict)", "info":"This is a dictionary of all the required python packages."}
    }

    #add perforce_helper settings definition
    igby_settings_definition.update(perforce_helper.p4_helper.p4_settings_defenition)

    os.system('cls')
    os.system('title Igby')
    igby_start_time = int(time.time())

    settings = igby_lib.get_settings(settings_json_file)
    python_dir = igby_lib.get_current_script_dir()

    #init logger
    logger = igby_lib.logger(settings["LOG_PATH"])

    #output location of settings file and containing settings for reference
    logger.log(f"Settings File Path: {settings_json_file}")

    with open(settings_json_file, "r") as file:

        for line in file:
            logger.log(line.replace("\n",""))
        
        logger.log("")

    #validate settings
    settings = igby_lib.validate_settings(settings, igby_settings_definition, logger)
   
    #setup PY_LIBS
    prerequisites_lib.setup_prerequisites(settings, logger)

    run_count = 0
    update_run_count = 0
    average_update_run_time = 0.0
    max_runs = settings["MAX_RUNS"]
    min_wait_sec = settings["MIN_WAIT_SEC"]
    ue_cmd_exe_path = settings["UE_CMD_EXE_PATH"]
    ue_project_path = settings["UE_PROJECT_PATH"]
    
    #start main loop
    while True:

        logger.reset_startup()

        success = True
        changes = False
        highest_cl = 0

        run_start_time = int(time.time())
        run_count+=1
        date_time = igby_lib.get_datetime()
        igby_elapsed_time = (run_start_time - igby_start_time)

        os.system(f'title Igby v{__version__} Total Runs:{run_count} Updated Runs:{update_run_count} Updated Run Average:{int(average_update_run_time)}s Elapsed:{(igby_elapsed_time/3600.0):.2f}h')

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
            exec(f"import {pre_run_python_command.split('.')[0]}")
            pre_run_command_result = eval(pre_run_python_command)

            # Pre Run Command result should be an array with 3 elements. 
            # Element 1 is a bool which dictates if pre_run_python_command execution was successful and process should continue.
            # Element 2 is a bool which dictates whether there was an update which should result in execution of Igby modules.
            # Element 3 is a string with info that you may want to output to log.
            if(pre_run_command_result[1]):
                logger.log("Pre Run Command resulted in the following update which will trigger module execution for this run.")
                logger.log(pre_run_command_result[2])
                pre_run_update = True

            if not pre_run_command_result[0]:
                return False
        
        logger.log("")
        logger.log(logger.add_characters(" Perforce Syncing. Please don't interrupt the process!", " ", header_str_len), "p4_h_clr")
        logger.log("")

        #init perforce
        if 'p4' not in locals():
            logger.log("Initializing Perforce.")
            logger.log("")
            p4 = perforce_helper.p4_helper(settings, logger)

        #test p4 connection
        if not p4.connected:
            logger.log("Perforce connection could not be established! Will try again during next run.", "error_clr")
            logger.log("")
            success = False
        else:
            #Sync to latest
            p4_dirs_to_sync = settings["P4_DIRS_TO_SYNC"]

            for p4_dir_to_sync in p4_dirs_to_sync:

                logger.log("\t{}".format(p4_dir_to_sync))
                results = p4.get_latest(p4_dir_to_sync)

                have_cl = 0

                if results == []:                    
                    have_cl = int(p4.get_have_changelist_number(p4_dir_to_sync))
                    logger.log(f"\t\tAlready have latest changelist {have_cl}")
                else:
                    have_cl = int(results[0]["change"])
                    changes = True
                    logger.log("\t\tSynced")
                    logger.log("\t\tHead CL: {} File Count: {} Total Size: {}".format(have_cl, results[0]["totalFileCount"], results[0]["totalFileSize"]))

                    if have_cl > highest_cl:
                        highest_cl = have_cl

            logger.log("")
            logger.log(logger.add_characters(" Perforce Syncing Completed.", " ", header_str_len),"p4_h_clr")

            #UGS Sync
            if "UGS_EXE_PATH" in settings:
            
                ugs = ugs_lib.ugs(logger, settings["UGS_EXE_PATH"], os.path.dirname(settings["UE_PROJECT_PATH"]))
                ugs_cl = ugs.sync()

                if ugs_cl == 0:
                    logger.log("Error! UGS experienced an error. Will try again during next run.","error_clr")
                    success = False
                    continue
                elif ugs_cl < 0:
                    ugs_cl = ugs_cl * -1
                    logger.log("UGS Sync: No updates available.")
                else:
                    changes = True

                if ugs_cl > highest_cl:
                    highest_cl = ugs_cl

            #Only run if there were changes to sync or pre run
            if changes or pre_run_update or settings["FORCE_RUN"]:

                post_sync_start_time = int(time.time())

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

                cmd = '"{}" "{}" SILENT -stdout -FullStdOutLogOutput -run=pythonscript -script="import igby; igby.run_modules(\'{}\',\'{}\',\'{}\',{})"'.format(ue_cmd_exe_path, ue_project_path, settings_json_file_ds, highest_cl, p4.p4.password, header_str_len)

                if debug:
                    logger.log("cmd = {}".format(cmd))
                try:
                    #setup pythonpath env var and run cmd
                    my_env = os.environ.copy()

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

                elapsed_update_time = int(time.time()) - post_sync_start_time
                average_update_run_time = (average_update_run_time * update_run_count + elapsed_update_time) / (update_run_count+1)
                update_run_count+=1

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

        

def run_modules(settings_json_file, synced_cl, p4_password, header_str_len):

    success = True

    try:

        import unreal, igby_lib, inspect

        settings = igby_lib.get_settings(settings_json_file)

        logger = igby_lib.logger()

        p4 = perforce_helper.p4_helper(settings, logger, p4_password)

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

            module_name = list(module_dict.keys())[0]

            module_settings = {}

            #introduce module default settings
            if "INCLUDE_MODULE_SETTING_PRESETS" in module_dict[module_name]:

                for module_setting_preset in module_dict[module_name]["INCLUDE_MODULE_SETTING_PRESETS"]:

                    if module_setting_preset in settings["MODULE_SETTING_PRESETS"]:

                        module_settings.update(settings["MODULE_SETTING_PRESETS"][module_setting_preset])
                    
                    else:

                        logger.log_ue(f"Error! The following module setting preset is not defined in \"MODULE_SETTING_PRESETS\" setting: {module_setting_preset}", "error_clr")
                        return False

                del module_dict[module_name]["INCLUDE_MODULE_SETTING_PRESETS"]

            #get and set module specific settings
            module_settings.update(module_dict[module_name])
            module_dict[module_name] = module_settings

            module_success = True

            if "REPORT_FILE_NAME_POSTFIX" in module_dict[module_name]:
                module_dict[module_name]["REPORT_FILE_NAME_POSTFIX"] += f'_CL{synced_cl}'
            else:
                module_dict[module_name]["REPORT_FILE_NAME_POSTFIX"] = f'_CL{synced_cl}'

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


if __name__ == "__main__":

    debug_flag = False

    if len(sys.argv) == 3 and sys.argv[2] == "-d":
        debug_flag = True

    run(sys.argv[1], debug=debug_flag)