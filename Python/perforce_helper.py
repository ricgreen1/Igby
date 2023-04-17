# perforce_helper.py for Igby UE Project Automator
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import sys, os, getpass, igby_lib

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
        
        self.p4.port = validated_settings["P4_PORT"]
        self.p4.user = validated_settings["P4_USER"]
        self.p4.client = validated_settings["P4_CLIENT"]
        self.p4.charset = validated_settings["P4_CHARSET"]
        self.cl_descsription_prefix = validated_settings["P4_CL_DESCRIPTION_PREFIX"]

        if p4_password != "":
            self.p4.password = p4_password
        else:
            self.p4.password = getpass.getpass("Perforce Password:")

        self.logger = logger

        self.connected = self.connect()
        self.file_info_cached = False
        info = self.p4.run("info")[0]
        self.client_root = info['clientRoot']
        self.depot_root = info['clientStream']
        self.client_root_l = f"{self.client_root.lower()}/".replace("\\","/")
        self.depot_root_l = f"{self.depot_root.lower()}/"

    #general functions

    def connect(self):

        connected = self.p4.connected()

        if not connected:

            try:
                self.p4.connect()
                connected = self.p4.connected()
                if connected:
                    if self.p4.password != "":
                        self.p4.run_login()
            except P4Exception:
                for errors in self.p4.errors:
                    print(errors)

        return connected


    #file functions

    def build_filelog_cache(self):

        self.logger.log("Building filelog cache.")

        self.depot_filelog = dict()

        filelogs = self.p4.run_filelog(f"{self.client_root}/...")

        for filelog in filelogs:
            self.depot_filelog[filelog.depotFile.lower()] = [filelog]

        self.file_info_cached = len(self.depot_filelog) > 0

        self.logger.log(f"Gathered filelog info for {len(self.depot_filelog)} files.")

    
    def get_filelog(self, path):

        path_l = self.convert_to_depot_path(path)

        filelog = None

        if self.file_info_cached:
            
            if path_l in self.depot_filelog:
                filelog = self.depot_filelog[path_l]
        
        #if info is not present in file_info cache, then fallback to get it directly from p4
        if filelog == None:
            filelog = self.p4.run_filelog(path)

        return filelog

    def get_latest(self, path, force = False, version = -1):
        
        if version > -1:
            path = "{}#{}".format(path,version)

        if force:
            results = self.p4.run("sync", "-q", "-f", path)
        else:
            results = self.p4.run("sync", "-q", path)

        return results
    

    def get_file_owner(self, path):

        owner = "Unknown"

        if self.is_file_in_depot(path):

            changes = self.p4.run_changes(path)
            
            if len(changes):
                owner = changes[-1]['user']

        return owner


    def get_file_history(self, path):

        histroy = self.get_filelog(path)

        return histroy


    def get_file_user(self, path, mode = "last"):

        if mode != "last" and mode != "best":

            raise Exception("mode parameter should be either \"last\" or \"best\"")

        last_user = "unknown"

        if self.is_file_in_depot(path):

            if mode == "last":

                filelog = self.get_filelog(path)

                if len(filelog):

                    last_user = filelog[0].revisions[-1].user

            elif mode == "best":

                #This will require a bit of logic that will try to figure out which user is the main contributer to the file.
                last_user = 'best'

        return last_user

    
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

    
    def is_file_in_depot(self, file):

        in_depot = False

        depot_path = self.convert_to_depot_path(file)
        if depot_path in self.depot_filelog:
            in_depot = True

        return in_depot


    def convert_to_depot_path(self, path):

        path_l = path.lower().replace("\\","/")
        path_l = path_l.replace(self.client_root_l, self.depot_root_l)
        return path_l

    
    def check_out_file(self, file, changelist_number = 0):

        checked_out = False

        if self.is_file_in_depot(file):

            changelist_number = str(changelist_number)

            result = self.p4.run("edit", "-c", changelist_number, file)

            if result[0]['action'] == 'edit':
                checked_out = True

        return checked_out

       

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

        local_files = []

        for file in files:

            local_files.append(file["path"].replace("\\","/"))

        return local_files