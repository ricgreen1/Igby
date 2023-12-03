# perforce_helper.py for Igby UE Project Automator
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import sys, os, getpass, igby_lib, datetime

#Add Perforce lib to path
current_script_dir = igby_lib.get_current_script_dir()

perforce_version_supported = False

if sys.version_info[0] == 3:

    if sys.version_info[1] == 9:
        perforce_script_dir = '{}/PerforceLib_3.9/site-packages'.format(current_script_dir)
        perforce_version_supported = True

    elif sys.version_info[1] == 7:
        perforce_script_dir = '{}/PerforceLib_3.7/site-packages'.format(current_script_dir)
        perforce_version_supported = True

if not perforce_version_supported:
    raise Exception("Perforce library requires python 3.7 or 3.9.")
        

#This will allow for exclusion of included perforce library if the included PerforceLib_3.9 directory is deleted.
if os.path.isdir(perforce_script_dir):
    sys.path.append(perforce_script_dir)

from P4 import P4, P4Exception

class p4_helper:

    p4_settings_defenition = {
    "P4_PORT":{"type":"str", "info":"Perforce server address and port. ex: 111.222.333.444:1666"},
    "P4_USER":{"type":"str", "info":"Perforce user name."},
    "P4_CLIENT":{"type":"str", "info":"Perforce client spec name."},
    "P4_CHARSET":{"type":"str", "default":"utf8", "info":"Character encoding spec."},
    "P4_PASSWORD":{"deprecated":"To improve security the perforce password must be entered manually."},
    "P4_CL_DESCRIPTION_PREFIX":{"type":"str", "default":"#igby_automation", "info":"Perforce changelist description prefix. ex: #igby_automation"}
    }

    def __init__(self, settings, logger, p4_password=""):

        validated_settings = igby_lib.validate_settings(settings, self.p4_settings_defenition, logger)

        self.p4 = P4()
        self.logger = logger

        self.p4.port = validated_settings["P4_PORT"]
        self.p4.user = validated_settings["P4_USER"]
        self.p4.client = validated_settings["P4_CLIENT"]
        self.p4.charset = validated_settings["P4_CHARSET"]
        self.cl_descsription_prefix = validated_settings["P4_CL_DESCRIPTION_PREFIX"]

        self.password = p4_password
        if self.password == "":
            self.password = getpass.getpass("Perforce Password:")

        self.connect()
        self.file_info_cached = False
        info = self.p4.run("info")[0]
        self.client_root = info['clientRoot']
        self.depot_root = info['clientStream']
        self.client_root_l = f"{self.client_root.lower()}/".replace("\\","/")
        self.depot_root_l = f"{self.depot_root.lower()}/"

        #for caching p4 info
        self.depot_filelog = {}
        self.changelist_files = {}
        self.depot_changes = {}

    #general functions
    def connect(self):

        connected = self.p4.connected()
        connection_info = None

        if not connected:

            try:
                connection_info = self.p4.connect()
                connected = self.p4.connected()
            except P4Exception:
                for error in self.p4.errors:
                    self.logger.log(error)

        if connected:

            self.logger.log("Connection Successful:")

            if not self.loggedin():

                if self.password == "":
                    self.password = getpass.getpass("Perforce Password:")

                self.logger.log("Executing p4 login.")
                self.p4.password = self.password
                login_info = self.p4.run_login()

                if not self.loggedin():
                    self.logger.log("Login Unsuccessful:")
                    self.logger.log(login_info)
                    connected = False
                else:
                    self.logger.log("Login Successful:")
        else:

            self.logger.log("Connection Unsuccessful:")
            self.logger.log(connection_info)

        return connected

    def connected(self):
        return self.p4.connected()
    
    def loggedin(self):

        logged_in = False

        try:
            login_info = self.p4.run_login("-s")
            ticket_expiration =  int(login_info[0]['TicketExpiration'])

            if ticket_expiration > 0:
                logged_in = True
        except:
            pass

        return logged_in


    #file functions

    def build_filelog_cache(self, paths = [None]):

        filelogs = list()

        for path in paths:

            path = path.replace("\\","/")

            if not path:
                path = f"{self.client_root}/..."
            else:
                path = f"{path}/..."

            self.logger.log(f"Building filelog cache for: {path}")

            filelogs = self.p4.run_filelog(path)

            progress_bar = igby_lib.long_process(len(filelogs), self.logger)

            for filelog in filelogs:
                depot_file_l = filelog.depotFile.lower()
                self.depot_filelog[depot_file_l] = [filelog]

                for rev in filelog.revisions:

                    if rev.change in self.changelist_files:
                        self.changelist_files[rev.change].append(depot_file_l)
                    else:
                        self.changelist_files[rev.change] = [depot_file_l]

                progress_bar.make_progress()

            file_log_count = len(filelogs)
            self.file_info_cached = file_log_count > 0
            self.logger.log(f"Cached {file_log_count} files")

    
    def build_changelist_cache(self, path = None):

        if not path:
            path = f"{self.client_root}/..."
        else:
            path = f"{path}/..."

        self.logger.log("Building changelist cache.")

        changes = self.p4.run_changes("-l", "-s", "submitted")

        progress_bar = igby_lib.long_process(len(changes), self.logger)

        for change in changes:
            self.depot_changes[change["change"]] = change
            progress_bar.make_progress()

        changes_count = len(self.depot_changes)
        self.change_info_cached = changes_count > 0
        self.logger.log(f"Gathered changelist info for {changes_count} changelists.")

    
    def get_filelog(self, path):

        filelog = None

        if self.file_info_cached:

            path_l = self.convert_to_depot_path(path)

            if path_l in self.depot_filelog:
                filelog = self.depot_filelog[path_l]
        
        if filelog == None:

            try:
                files = self.p4.run_files(path)

                if files is list and len(files) > 0:
                    filelog = self.p4.run_filelog(path)

                    self.logger.log(f"Path not found in filelog cache: {path}", "warning_clr")
                    self.logger.log(f"Make sure to run filelog caching on all necessary paths to speedup perforce queries.", "warning_clr")
            except:
                pass

        return filelog

    def get_latest(self, path, force = False, version = -1):
        
        if version > -1:
            path = "{}#{}".format(path,version)

        if force:
            results = self.p4.run("sync", "-q", "-f", path)
        else:
            results = self.p4.run("sync", "-q", path)

        return results
    

    def get_file_history(self, path):

        histroy = self.get_filelog(path)

        return histroy
    

    def get_file_owner(self, path):

        owner = None

        if self.is_file_in_depot(path) and not self.is_file_available_for_checkout(path):

            fstat = self.p4.run('fstat', path)[0]

            if 'actionOwner' in fstat:
                owner = fstat['actionOwner']
            else:
                if 'otherOpen' in fstat:
                    other_open = fstat['otherOpen']
                    if len(other_open) > 0:
                        owner = other_open[0]
                        for other_owner in other_open[1:]:
                            owner = f"{owner},{other_owner}"

        return owner


    def get_file_user(self, path, mode = "last"):

        if mode != "last" and mode != "best" and mode != "both":

            raise Exception("mode parameter should be either \"last\" or \"best\"")

        user = None
        last_user = None
        best_user = None

        if self.is_file_in_depot(path):

            filelog = self.get_filelog(path)

            if len(filelog):

                if mode == "last" or mode == "both":

                    last_user = filelog[0].revisions[0].user

                if mode == "best" or mode == "both":

                    users = dict()
                    cur_time = datetime.datetime.timestamp(datetime.datetime.now())

                    for rev in filelog[0].revisions:
                        #ignore users
                        #ignore changelist hashtag
                        #ignore changelist numbers

                        #cl file count
                        cl_file_count = len(self.changelist_files[rev.change])
                        cl_file_count_w = pow((1.0/cl_file_count),0.5)

                        #elapsed time
                        file_time = datetime.datetime.timestamp(rev.time)
                        elapsed_time = cur_time - file_time
                        elapsed_time_d = max((elapsed_time / 86400.0), 1.0)
                        elapsed_time_d_w = pow((1.0/elapsed_time_d),0.5)

                        weight = (cl_file_count_w + elapsed_time_d_w)

                        if rev.user in users:
                            users[rev.user] += weight
                        else:
                            users[rev.user] = weight

                    users_sorted = sorted(users.items(), key=lambda x:x[1])
                    best_user = users_sorted[-1][0]

        if mode == "last":
            user = last_user
        elif mode == "best":
            user = best_user
        elif mode == "both":
            if best_user == last_user:
                user = last_user
            else:
                user = f"best:{best_user} last:{last_user}"

        return user


    def get_file_date(self, path, mode = "last", format = True):

        last_date = None

        if self.is_file_in_depot(path):

            filelog = self.get_filelog(path)

            if len(filelog):
                if mode == "last":
                    last_date = filelog[0].revisions[0].time
                elif mode == "first":
                    last_date = filelog[0].revisions[-1].time

            if format:
                last_date = last_date.strftime("%Y/%m/%d %H:%M")
            else:
                last_date = datetime.datetime.timestamp(last_date)

        return last_date
    
    
    def is_file_available_for_checkout(self, path, exclusive = True):

        available = False

        if self.is_file_in_depot(path):

            fstat = self.p4.run('fstat', path)[0]

            if exclusive and 'otherOpen' in fstat:
                available = False
            elif 'action' in fstat:
                available = False
            else:
                available = True

        return available

    def is_file_checked_out_by_me(self, path):

        checked_out_by_me = False

        if self.is_file_in_depot(path):

            fstat = self.p4.run('fstat', path)[0]

            if 'action' in fstat:
                checked_out_by_me = True

        return checked_out_by_me

    
    def is_file_in_depot(self, path):

        file_log = self.get_filelog(path)
        in_depot = file_log != None

        return in_depot


    def convert_to_depot_path(self, path):

        path_l = path.lower()

        if not path_l.startswith("//"):
            path_l = path_l.replace("\\","/")
            path_l = path_l.replace(self.client_root_l, self.depot_root_l)
        
        return path_l

    
    def check_out_file(self, path, changelist_number = 0):

        checked_out = False

        if self.is_file_in_depot(path):

            changelist_number = str(changelist_number)

            result = self.p4.run("edit", "-c", changelist_number, path)

            if result[0]['action'] == 'edit':
                checked_out = True

        return checked_out


    def mark_for_delete(self, path, changelist_number = 0):

        marked_for_delete = False

        if self.is_file_in_depot(path):

            changelist_number = str(changelist_number)

            result = self.p4.run("delete", "-c", changelist_number, path)

            if result[0]['action'] == 'delete':
                marked_for_delete = True

        return marked_for_delete

    #Changelist functions


    def create_changelist(self, description):

        description = "{} {}".format(self.cl_descsription_prefix, description)

        changelist = int(self.p4.save_change({'Change': 'new', 'Description': description})[0].split()[1])

        return changelist


    def get_have_changelist_number(self, path):

        have_changelist_number = 0

        if "\\" in path and not path.endswith("\\"):

            path += "\\"

        elif "/" in path and not path.endswith("/"):

            path += "/"

        path += "...#have"

        result = self.p4.run_changes("-m1", path)
        have_changelist_number = result[0]["change"]

        return have_changelist_number


    def get_client_changelists(self):

        changelist_numbers = []
        client_changes = self.p4.run_changes("-s", "pending", "-c", self.p4.client)

        for change in client_changes:
            changelist_numbers.append(int(change["change"]))

        return changelist_numbers


    def get_changelist_files(self, changelist_number):

        changelist_number = str(changelist_number)
        files = self.p4.run('opened','-c', changelist_number)
        changelist_files = []

        for file in files:

            where = self.p4.run_where(file['depotFile'])
            changelist_files.append(where[0]['path'])

        return changelist_files


    def set_changelist_description(self, changelist_number, description):

        changelist_number = str(changelist_number)
        changelist = self.p4.fetch_change(changelist_number)
        changelist['Description'] = description
        self.p4.save_change(changelist)
    

    def get_changelist_description(self, changelist_number):

        changelist_number = str(changelist_number)
        changelist = self.p4.fetch_change(changelist_number)
        changelist_description = changelist['Description']

        return changelist_description


    def revert_changelist_files(self, changelist_number, only_revert_unchanged = False):

        changelist_number = str(changelist_number)
        files = self.get_changelist_files(changelist_number)

        if len(files):

            if(only_revert_unchanged):
                result = self.p4.run("revert", "-a", "-c", changelist_number, "//...")
            else:
                result = self.p4.run("revert", "-c", changelist_number, "//...")

        else:
            result = None

        return result


    def delete_changelist(self, changelist_number):

        changelist_number = str(changelist_number)

        if self.get_changelist_status(changelist_number) == "pending":
            result = self.p4.run("change", "-d", changelist_number)
        else:
            result = None

        return result


    def submit_changelist(self, changelist_number):

        changelist_number = str(changelist_number)

        if self.get_changelist_status(changelist_number) == "pending":
            result = self.p4.run_submit( "-c", changelist_number )
        else:
            result = None

        return result


    def get_changelist_status(self, changelist_number):

        changelist_number = str(changelist_number)
        changelist = self.p4.fetch_change(changelist_number)
        status = changelist["Status"]

        return status


    def move_to_changelist(self, files, changelist_number):

        changelist_number = str(changelist_number)
        status = self.p4.run_reopen('-c', changelist_number, files)

        return status


    def get_have_files_in_folder(self, folder):

        files = []

        folder = folder.replace("\\","/")

        try:

            if folder[-1] == "/":
                folder = f"{folder}..."
            else:
                folder = f"{folder}/..."

            files = self.p4.run('have', folder)

        except:
            pass

        local_files = [x["path"].replace("\\","/") for x in files]

        return local_files