# ugs_lib.py | This library uses ugs.exe cli to access Unreal Game Sync functionality.
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import os, subprocess, time

class ugs:

    def __init__(self, logger, p4, ugs_exe_path, client_root):
        
        self.ugs_exe_path = ugs_exe_path
        self.client_root = client_root
        self.logger = logger
        self.p4 = p4
        self.ugs_debug_log = "UGS DEBUG LOG:\n"

    def sync(self, submitted_changelist = 0):

        if not self.p4.connected():
            return -1

        self.ugs_debug_log+="\nRunning sync"

        success = False

        self.current_cl = self.get_current_cl()
        self.latest_cl = self.get_latest_cl()

        if self.current_cl == -1 or self.latest_cl == -1:
            return -1
        
        incomplete_sync = False
        if self.current_cl < -1:
            self.current_cl*=-1
            incomplete_sync = True

        self.logger.log(f"Syncing via UGS")

        if incomplete_sync:
            self.logger.log(f"Current CL is {self.current_cl}, but the sync was incolplete.")
        else:
            self.logger.log(f"Current CL is {self.current_cl}")

        self.logger.log(f"Latest available CL is {self.latest_cl}")
        self.synced_cl = 0
        self.critical_error = False

        #check to see if latest available cl is at igby submitted cl or newer.
        if self.latest_cl < submitted_changelist:
            self.logger.log(f"Skipping because latest available CL:{self.latest_cl} is older than last Igby submitted CL:{submitted_changelist}")
            return (self.latest_cl * -1)

        if self.latest_cl > self.current_cl or incomplete_sync and self.latest_cl == self.current_cl:

            self.logger.log(f"Syncing {self.latest_cl}. Please don't interrupt the process.", "warning_clr")

            #Sync latest
            os.chdir(self.client_root)
            cmd = f"{self.ugs_exe_path} sync {self.latest_cl} -binaries"

            success = False
            build_not_ready = False
            tries = 0
            max_tries = 20
            sleep = 60

            ignore_strings = ["Removing ", "Writing ", "Added ", "Updated ", "Deleted"]

            while not success:

                binaries_unavailable = False

                tries+=1

                process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

                while process.poll() is None:
                    stdout_line = str(process.stdout.readline())

                    if "error" in stdout_line.lower():
                        log_error = True

                        for ignore_string in ignore_strings:
                            if ignore_string in stdout_line:
                                log_error = False
                                break

                        if log_error:
                            self.logger.log(stdout_line)

                    self.ugs_debug_log = f"{self.ugs_debug_log}{stdout_line}"
                    if "UPDATE SUCCEEDED" in stdout_line:
                        success = True
                    elif "No editor binaries found" in stdout_line:
                        binaries_unavailable = True
                        self.logger.log(f"Try #{tries}/{max_tries} Editor binaries unavailable. Waiting {sleep} sec.", "warning_clr")
                        time.sleep(sleep)
                        break

                process.stdout.close()

                if tries > max_tries: #max tries

                    self.logger.log(f"Max tries attempted. Skipping UGS sync.", "warning_clr")
                    build_not_ready = True
                    break

                if not success and not binaries_unavailable and not build_not_ready:
                    self.logger.log(f"Try #{tries}/{max_tries} Something went wrong. Waiting {sleep} sec.", "warning_clr")
                    time.sleep(sleep)

            if success:
                self.synced_cl = self.latest_cl
            elif build_not_ready:
                self.synced_cl = self.latest_cl * -1
            else:
                self.critical_error = True
                self.ugs_debug_log = f"{self.ugs_debug_log}\nSynch operation was not successful."
                
        else:
            
            if self.current_cl == 0 or self.latest_cl == 0:
                self.synced_cl = self.latest_cl * -1
                self.ugs_debug_log = f"{self.ugs_debug_log}\nReported changelists are inconsistent: Current{self.current_cl} Latest{self.latest_cl}"
            else:
                self.synced_cl = self.latest_cl * -1

        if self.critical_error:
            self.logger.log(f"UGS sync error! Check Igby log for more info: {self.logger.log_path}", "error_clr")
            self.logger.log(self.ugs_debug_log, "normal_clr", False, True)
            raise(Exception("UGS experienced a critical error. Stopping Igby execution until the issue is adressed."))

        return self.synced_cl


    def get_current_cl(self):

        if not self.p4.connected():
            return -1

        self.ugs_debug_log+="\nRunning get_current_cl"

        os.chdir(self.client_root)
        cmd = f"{self.ugs_exe_path} status"
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        cur_cl = 0

        while process.poll() is None:
            stdout_line = str(process.stdout.readline())
            self.ugs_debug_log = f"{self.ugs_debug_log}{stdout_line}"

            if "CL" in stdout_line:

                cur_cl = int(stdout_line.split(" CL ")[-1].split(" ")[0].split("\\")[0])

                if "failed" in stdout_line:
                    cur_cl = cur_cl * -1

        process.stdout.close()

        return cur_cl


    def get_latest_cl(self):

        if not self.p4.connected():
            return -1

        self.ugs_debug_log+="\nRunning get_latest_cl"

        os.chdir(self.client_root)
        cmd = f"{self.ugs_exe_path} changes"
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        latest_cl = 0

        while process.poll() is None:
            stdout_line = str(process.stdout.readline())
            self.ugs_debug_log = f"{self.ugs_debug_log}{stdout_line}"

            try:
                latest_cl = int(stdout_line.split(" ")[2])
            except:
                pass

            if latest_cl > 0:
                break

        process.stdout.close()

        return latest_cl