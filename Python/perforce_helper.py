# perforce_helper.py for Igby UE Project Automator
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import sys, os, getpass, igby_lib

#Add Perforce lib to path
current_script_dir = igby_lib.get_current_script_dir()
perforce_script_dir = '{}/PerforceLib_3.9/site-packages'.format(current_script_dir)

#This will allow for exclusion of included perforce library if the included PerforceLib_3.9 directory is deleted.
if os.path.isdir(perforce_script_dir):
    sys.path.append(perforce_script_dir)

from P4 import P4, P4Exception

class p4_helper:

    p4 = P4()

    def __init__(self, port, user, client, password="", cl_descsription_prefix = ""):
        
        self.port = port
        self.user = user
        self.client = client
        self.password = password
        self.cl_descsription_prefix = cl_descsription_prefix

        self.connected = self.connect()

    #general functions

    def connect(self):

        connected = self.p4.connected()

        if not connected:
            self.p4.port = self.port
            self.p4.user = self.user
            self.p4.client = self.client

            if self.password == "":
                self.p4.password = getpass.getpass("Please Enter Perforce Password:")
            else:
                self.p4.password = self.password

            try:
                print('Connecting to Perforce')
                self.p4.connect()
                connected = self.p4.connected()
                if self.p4.password != "":
                    self.p4.run_login()
            except P4Exception:
                for errors in self.p4.errors:
                    print(errors)

        return connected


    #file functions

    def get_latest(self, path, force = False, version = -1):
        
        if version > -1:
            path = "{}#{}".format(path,version)

        if force:
            results = self.p4.run("sync", "-q", "-f", path)
        else:
            results = self.p4.run("sync", "-q", path)

        return results


    def get_file_owner(self, path):

        owner = None

        changes = self.p4.run_changes(path)
        
        if len(changes):
            owner = changes[-1]['user']

        return owner


    def is_file_available_for_checkout(self, path, exclusive = True):

        available = True

        fstat = self.p4.run('fstat', path)[0]

        if exclusive and 'otherOpen' in fstat:
            available = False

        elif 'action' in fstat:
            available = False

        return available

    def is_file_checked_out_by_me(self, path):

        checked_out_by_me = False

        fstat = self.p4.run('fstat', path)[0]

        if 'action' in fstat:
            checked_out_by_me = True

        return checked_out_by_me

    
    def is_file_in_depot(self, file):

        in_depot = True

        try:
            self.p4.run('files',file)
        except:
            in_depot = False

        return in_depot

    
    def check_out_file(self, file, changelist_number = 0):

        checked_out = False

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