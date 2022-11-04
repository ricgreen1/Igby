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
                    logger.log(results)
                    logger.log("\t\tSynced")
                    for cl in results:
                        logger.log("\t\tHead CL: {} File Count: {} Total Size: {}".format(cl["change"], cl["totalFileCount"], cl["totalFileSize"]))

            logger.log("")
            logger.log(logger.add_characters(" Perforce Syncing Completed.", " ", header_str_len),"p4_h_clr")

            #Only run if there were changes to sync or pre run
            if changes or pre_run_update or settings["FORCE_RUN"]:
            
                #launch headless UE and run command
                ue_cmd_exe_path = settings["UE_CMD_EXE_PATH"]
                ue_project_path = settings["UE_PROJECT_PATH"]
                settings_json_file_ds = settings_json_file.replace('\\','/')

                cmd = '"{}" "{}" SILENT -stdout -FullStdOutLogOutput -run=pythonscript -script="import igby; igby.run_modules(\'{}\',{})"'.format(ue_cmd_exe_path, ue_project_path, settings_json_file_ds, header_str_len)

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

                    pid = str(process.pid)
                    igby_lib.encode_str(p4.p4.password, pid)

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

        

def run_modules(settings_json_file, header_str_len):

    import inspect, unreal, igby_lib, ue_asset_lib

    settings = igby_lib.get_settings(settings_json_file)

    logger = igby_lib.logger()

    parent_pid = str(os.getppid())
    p4_password = igby_lib.decode_str(parent_pid)

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

    #Check for assets that are not in perforce
    logger.log_ue("Testing project content integrity.\n")
    project_integrity_report = ""
    rel_content_path = unreal.Paths.project_content_dir()
    abs_content_path = unreal.Paths.convert_relative_path_to_full(rel_content_path)

    have_files = set(p4.get_have_files_in_folder(abs_content_path))

    all_assets = asset_registry.get_assets_by_path("/Game", True, True)

    local_files = set()

    for asset in all_assets:

        system_path = ue_asset_lib.get_package_system_path(asset.package_name)
        local_files.add(system_path)

    local_files_not_in_depot = list(local_files - have_files)

    if len(local_files_not_in_depot):
        
        files = " NID\n".join(local_files_not_in_depot)
        project_integrity_report = f"The following project files are present locally but are not in the depot:\n\n{files}"

    depot_files_not_in_local = have_files - local_files

    if len(depot_files_not_in_local):

        files = " NIL\n".join(depot_files_not_in_local)
        project_integrity_report = f"{project_integrity_report}\nThe following project files are in depot but are not present locally.\n\n{files}"

    if len(local_files_not_in_depot) or len(depot_files_not_in_local):

        error_log_path = igby_lib.dump_error(project_integrity_report)
        logger.log_ue("Halting igby run due to project content inconsistencies.\nDetailed information can be found in in this report: {}".format(error_log_path), "error_clr")
    else:
        logger.log_ue("Project content integrity within norm.")

    #Run modules
    for module_dict in modules_to_run:

        #introduce module default settings
        module_name = list(module_dict.keys())[0]

        if "MODULE_DEFAULT_SETTINGS" in settings:

            for module_default_setting in settings["MODULE_DEFAULT_SETTINGS"]:

                if module_default_setting not in module_dict[module_name]:

                    module_dict[module_name][module_default_setting] = settings["MODULE_DEFAULT_SETTINGS"][module_default_setting]

        success = True

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

            success = False
            error_message = traceback.format_exc()
            logger.log_ue(error_message, "error_clr")

        if success:
            logger.log_ue("\n [ {}s ] ".format(elapsed_time), "success_h_clr")
        else:
            logger.log_ue("\n [ {}s ] {} Failed ".format(elapsed_time, module_name), "failure_h_clr")
    
    return success


if __name__ == "__main__":

    debug_flag = False

    if len(sys.argv) == 3 and sys.argv[2] == "-d":
        debug_flag = True

    run(sys.argv[1], debug=debug_flag)