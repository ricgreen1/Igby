# ugs_lib.py | This library uses ugs.exe cli to access Unreal Game Sync functionality.
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import os, subprocess

class ugs:

    def __init__(self, logger, ugs_exe_path, client_root):
        
        self.ugs_exe_path = ugs_exe_path
        self.client_root = client_root
        self.logger = logger

    def sync(self):

        success = False

        self.current_cl = self.get_current_cl()
        self.latest_cl = self.get_latest_cl()

        self.logger.log(f"Syncing via UGS")
        self.logger.log(f"Current CL is {self.current_cl}")
        self.logger.log(f"Latest available CL is {self.latest_cl}")

        self.synced_cl = 0

        if self.latest_cl > self.current_cl:

            self.logger.log(f"Syncing {self.latest_cl}. Please don't interrupt the process.", "warning_clr")

            #Sync latest
            os.chdir(self.client_root)
            cmd = f"{self.ugs_exe_path} sync {self.latest_cl} -binaries"
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

            while process.poll() is None:
                stdout_line = str(process.stdout.readline())
                if "UPDATE SUCCEEDED" in stdout_line:
                    success = True

            process.stdout.close()

            if success:
                self.synced_cl = self.latest_cl
                
        else:
            self.synced_cl = self.latest_cl * -1

        return self.synced_cl


    def get_current_cl(self):

        os.chdir(self.client_root)
        cmd = f"{self.ugs_exe_path} status"
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        cur_cl = 0

        while process.poll() is None:
            stdout_line = str(process.stdout.readline())

            if "CL" in stdout_line:
                cur_cl = int(stdout_line.split(" ")[-1].split("\\")[0])

        process.stdout.close()

        return cur_cl


    def get_latest_cl(self):

        os.chdir(self.client_root)
        cmd = f"{self.ugs_exe_path} changes"
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        latest_cl = 0

        while process.poll() is None:
            stdout_line = str(process.stdout.readline())

            try:
                latest_cl = int(stdout_line.split(" ")[2])
            except:
                pass

            if latest_cl > 0:
                break

        process.stdout.close()

        return latest_cl