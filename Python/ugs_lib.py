# ugs_lib.py | This library uses ugs.exe cli to access Unreal Game Sync functionality.
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import os, subprocess, time

class ugs:

    def __init__(self, logger, ugs_exe_path, client_root):
        
        self.ugs_exe_path = ugs_exe_path
        self.client_root = client_root
        self.logger = logger
        self.ugs_debug_log = ""

    def sync(self):

        self.ugs_debug_log+="\nRunning sync"

        success = False

        self.current_cl = self.get_current_cl()
        self.latest_cl = self.get_latest_cl()
        self.ugs_debug_log = ""

        self.logger.log(f"Syncing via UGS")
        self.logger.log(f"Current CL is {self.current_cl}")
        self.logger.log(f"Latest available CL is {self.latest_cl}")

        self.ugs_debug_log = ""

        self.synced_cl = 0

        critical_error = False

        if self.latest_cl > self.current_cl:

            self.logger.log(f"Syncing {self.latest_cl}. Please don't interrupt the process.", "warning_clr")

            #Sync latest
            os.chdir(self.client_root)
            cmd = f"{self.ugs_exe_path} sync {self.latest_cl} -binaries"

            success = False
            tries = 0
            max_tries = 20
            sleep = 60

            while not success:

                binaries_unavailable = False

                tries+=1

                process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

                while process.poll() is None:
                    stdout_line = str(process.stdout.readline())
                    self.ugs_debug_log+=stdout_line
                    if "UPDATE SUCCEEDED" in stdout_line:
                        success = True
                    elif "No editor binaries found" in stdout_line:
                        binaries_unavailable = True
                        self.logger.log(f"Try #{tries}/{max_tries} Editor binaries unavailable. Waiting {sleep} sec.", "warning_clr")
                        time.sleep(sleep)
                        break

                process.stdout.close()

                if not success and not binaries_unavailable:
                    self.logger.log(f"Try #{tries}/{max_tries} Something went wrong. Waiting {sleep} sec.", "warning_clr")
                    time.sleep(sleep)

                if tries > max_tries: #max tries

                    self.logger.log(f"Max tries attempted. Skipping UGS sync.", "warning_clr")
                    break

            if success:
                self.synced_cl = self.latest_cl
            else:
                critical_error = True
                
        else:
            
            if self.current_cl == 0 or self.latest_cl == 0:
                critical_error = True
            else:
                self.synced_cl = self.latest_cl * -1

        if critical_error:
            self.logger.log(f"UGS sync error! Check Igby log for more info: {self.logger.log_path}", "error_clr")
            self.logger.log(self.ugs_debug_log, "normal_clr", False, True)
            raise(Exception("UGS experienced a critical error. Stopping Igby execution until the issue is adressed."))

        return self.synced_cl


    def get_current_cl(self):

        self.ugs_debug_log+="\nRunning get_current_cl"

        os.chdir(self.client_root)
        cmd = f"{self.ugs_exe_path} status"
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        cur_cl = 0

        while process.poll() is None:
            stdout_line = str(process.stdout.readline())
            self.ugs_debug_log+=stdout_line

            if "CL" in stdout_line:
                cur_cl = int(stdout_line.split(" ")[-1].split("\\")[0])

        process.stdout.close()

        return cur_cl


    def get_latest_cl(self):

        self.ugs_debug_log+="\nRunning get_latest_cl"

        os.chdir(self.client_root)
        cmd = f"{self.ugs_exe_path} changes"
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        latest_cl = 0

        while process.poll() is None:
            stdout_line = str(process.stdout.readline())
            self.ugs_debug_log+=stdout_line

            try:
                latest_cl = int(stdout_line.split(" ")[2])
            except:
                pass

            if latest_cl > 0:
                break

        process.stdout.close()

        return latest_cl