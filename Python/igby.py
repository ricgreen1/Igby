# igby.py Igby UE Project Automator
# Developed by Richard Greenspan | igby.rg@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

__version__ = "0.1.0"

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

        #connect to perforce
        p4 = perforce_helper.p4_helper(settings["P4_PORT"], settings["P4_USER"], settings["P4_CLIENT"], settings["P4_PASSWORD"])
        connected = p4.connect()
        logger.log("")
        if not connected:
            logger.log("Could not connect to perforce! Will try again in {} seconds.".format(min_wait_sec))
            continue

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
                my_env["UE_PYTHONPATH"] = "{};{}".format(python_dir, automation_modules_dir)

                process = subprocess.Popen(cmd, env=my_env, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

                logger.log("\nLaunching Headless Editor: {}".format(ue_cmd_exe_path))
                logger.log("Loading Project: {}".format(ue_project_path))
                logger.log("Loading a large project may take some time. Please be patient! :)")

                while process.poll() is None:
                    stdout_line = str(process.stdout.readline())
                    logger.log_filter_ue(stdout_line, debug)

                process.stdout.close()

            except Exception:

                error_message = traceback.format_exc()

                logger.log("ERROR During Unreal Engine Execution :(", "error_clr")
                error_message = traceback.format_exc()
                logger.log_ue(error_message, "error_clr")

                if settings["HALT_ON_ERROR"]:
                    logger.log("Igby execution halted due to error.")
                    return False
                else:
                    logger.log("Trying again.")
        else:
            logger.log("Skipping Run Because No Changes.")

        logger.log("\n")

        elapsed_time = int(time.time()) - run_start_time

        logger.log("Run #{} Completed In {} sec. :)\n".format(run_count, elapsed_time))

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

    settings = igby_lib.get_settings(settings_json_file)

    logger = igby_lib.logger()
    p4 = perforce_helper.p4_helper(settings["P4_PORT"], settings["P4_USER"], settings["P4_CLIENT"], settings["P4_PASSWORD"], settings["P4_CL_DESCRIPTION_PREFIX"])

    if not p4.connect():
        logger.log("Could not connect to perforce! Exiting.")
        success = False
        return success

    modules_to_run = settings["MODULES_TO_RUN"]

    for module_dict in modules_to_run:

        success = True

        try:

            module_name = list(module_dict.keys())[0]

            logger.log_ue("\n")
            logger.log_ue(logger.add_characters(" [ {} ]".format(module_name), " ", header_str_len), "module_h_clr")
            logger.log_ue("\n")

            module = importlib.import_module(module_name)
            module_run = getattr(module, 'run')
            module_start_time = int(time.time())

            module_run(module_dict[module_name], p4)

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