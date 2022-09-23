# sample_pre_run_command.py
# Developed by Richard Greenspan | ricgreen1@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

def run():

    # Pre Run Command result should be an array with 3 elements. 
    # Element 1 is a bool which dictates if pre_run_python_command execution was successful and process should continue.
    # Element 2 is a bool which dictates whether there was an update which should result in execution of modules.
    # Element 3 is a string with info that you may want to output to log.

    result = [True, False, "Operation completed successfully. :)"]

    #Do some work here
    work_completed_successfully = True
    update_occured = False

    if not work_completed_successfully:
        result = [False, False, "There was an error... :("]
    elif update_occured:
        result = [True, True, "Operation completed successfully and resulted in Engine Update... :)"]

    return result