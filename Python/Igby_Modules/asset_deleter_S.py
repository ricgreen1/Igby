# asset_deleter _S.py Module for Igby UE Project Automator
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import unreal, os, traceback, ue_asset_lib, igby_lib, module_settings

def run(settings_from_json, logger, p4):

    #get settings
    module_settings_definition = {"TASK_DIR":{"type":"string", "info":"Path to the Task directory."}}
    # module_settings_definition.update({"USER":{"type":"string", "info":"User that is requesting this task."}})
    # module_settings_definition.update({"CL_DESCIPTION":{"type":"string", "info":"Task description for the Perforce Changelist."}})
    # module_settings_definition.update({"MAX_BATCH_SIZE":{"type":"int", "optional":True, "info":"Task description for the Perforce Changelist."}})
    settings = igby_lib.validate_settings(settings_from_json, module_settings_definition, logger)

    task_dir = settings["TASK_DIR"]
    logger.log(f"Task Dir:{task_dir}")

    logger.log_ue("Running asset_deleter tasks.\n")

    logger.log_ue("Verifying and generating WORKING files.\n")

    for filename in os.listdir(task_dir):

        if filename.lower().endswith(".csv"):

            task_file = os.path.join(task_dir, filename)
            task_file_l = task_file.lower()

            if not task_file_l.endswith("_working.csv") and not task_file_l.endswith("_done.csv"):

                working_file = task_file.replace(".","_WORKING.")

                if os.path.isfile(working_file):
                    logger.log(f"Warning! Corresponding WORKING file already exists: {working_file}\nPlease change the task filename to remedy the clashing name.", "warning_clr")
                
                done_file = task_file.replace(".","_DONE.")

                if os.path.isfile(done_file):
                    logger.log(f"Warning! Corresponding DONE file already exists: {done_file}\nPlease change the task filename to remedy the clashing name.", "warning_clr")

                with open(task_file, "r") as task_f:

                    task_lines = task_f.readlines()
                    task_description = task_lines[0]
                    files_to_delete = list(set(task_lines[1:-1]))
                    files_to_delete.sort()

                os.rename(task_file, working_file)

                with open(working_file, "w") as task_f:

                    task_f.write(task_description)
                    task_f.writelines(files_to_delete)

    logger.log_ue("Processing WORKING files.\n")

    for filename in os.listdir(task_dir):

        if filename.lower().endswith("_working.csv"):

            working_file = os.path.join(task_dir, filename)
            logger.log_ue(f"Processing: {working_file}")



    return True

    

    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    dep_options = unreal.AssetRegistryDependencyOptions(include_soft_package_references=True, include_hard_package_references=True, include_searchable_names=False, include_soft_management_references=False, include_hard_management_references=False)

    all_assets = ue_asset_lib.get_assets(settings["PATHS_TO_INCLUDE"], settings["PATHS_TO_IGNORE"], True)
    redirector_filter = unreal.ARFilter(class_names=["ObjectRedirector"])
    all_redirectors = asset_registry.run_assets_through_filter(all_assets, redirector_filter)

    changelist_num = 0

    redirector_deleter_i = redirector_deleter(p4, logger)
    
    #find all redirectors
    
    all_filtered_redirector_packages = set()

    #filter redirectors that belong to package that contain non redirector assets.
    for redirector_object in all_redirectors:
        
        redirector_package_name = str(redirector_object.package_name)
        redirector_package_assets = asset_registry.get_assets_by_package_name(redirector_package_name)

        if len(redirector_package_assets)>1 and not ue_asset_lib.assets_class_only_test(redirector_package_assets, "ObjectRedirector"):
            logger.log_ue("Warning: Skipping redirector because it shares a package with a non redirector asset:", "warning_clr")
            logger.log_ue(f"Package: {redirector_package_name}", "warning_clr")
            continue

        all_filtered_redirector_packages.add(redirector_package_name)

    logger.log_ue("Identified {} Redirectors:".format(len(all_filtered_redirector_packages)))

    #Loop through all appropriate redirectors
    for redirector_package_name in all_filtered_redirector_packages:

        logger.prefix = "    "
        logger.log_ue("")
        logger.log_ue("Processing Redirector: {}".format(redirector_package_name))
        logger.prefix = "      "

        all_dependencies = ue_asset_lib.get_package_connections(redirector_package_name, "dependencies", True, True, True) 
        all_referencers = ue_asset_lib.get_package_connections(redirector_package_name, "referencers", True, True, True) 

        if ue_asset_lib.class_only_test(all_dependencies, "ObjectRedirector") or ue_asset_lib.class_only_test(all_referencers, "ObjectRedirector"):

            redirector_deleter_i.add_to_delete(redirector_package_name)

        else:

            redirector_object = asset_registry.get_assets_by_package_name(redirector_package_name)

            redirector_referencers = [*set(asset_registry.get_referencers(redirector_package_name, dep_options))]#this can be 0 or more assets. 0 means that that the redirector is not being used and can later be deleted.
            
            #Find redirector target.
            redirector_dependencies = asset_registry.get_dependencies(redirector_package_name, dep_options)#this should always be 0-1 assets. 0 assets means that the redirector is not valid and can later be deleted.

            #This accounts for situations where there is a redirector chain. This will find the asset that the chain is pointing at. If an asset is not found, then the redirector is marked for deletion.
            redirector_target_object = None

            #loop until we find a non redirector target
            while len(redirector_dependencies):

                target_object = asset_registry.get_assets_by_package_name(redirector_dependencies[0])[0]

                if target_object.is_redirector():
                    target_package_name = str(target_object.package_name)
                    redirector_dependencies = asset_registry.get_dependencies(target_package_name, dep_options)
                else:
                    redirector_target_object = target_object
                    break

            
            #Later we will determine if this redirector can be deleted.
            redirector_deleter_i.add_to_check(redirector_object)

            #Now that we have all the necessary elements, we will go ahead and clean up redirectors.
            for redirector_referencer in redirector_referencers:

                referencer_objects = asset_registry.get_assets_by_package_name(redirector_referencer)

                if len(referencer_objects) > 1 and not ue_asset_lib.assets_class_only_test(referencer_objects, "ObjectRedirector"):

                    logger.log_ue("Skipping redirector because it's referencer package ({}) contains more than 1 asset. Assets should be split up into individual packages.".format(referencer_object,))
                    break
                else:
                    referencer_object = referencer_object[0]

                referencer_object_path = ue_asset_lib.get_object_path(referencer_object)

                #connect referencer to target to avoid redirector.
                logger.log_ue("")
                logger.log_ue("Redirector Referencer: {}".format(redirector_referencer))

                referencer_asset = referencer_object.get_asset()
                referencer_sys_path = unreal.SystemLibrary.get_system_path(referencer_asset)
                referencer_package = unreal.find_package(redirector_referencer)

                # logger.log_ue("asset data: {}".format(referencer_object))
                # logger.log_ue("asset: {}".format(referencer_asset))
                # logger.log_ue("asset path: {}".format(referencer_sys_path))

                if p4.is_file_in_depot(referencer_sys_path):

                    if p4.is_file_available_for_checkout(referencer_sys_path):

                        try:
                            checked_out = False

                            #create changelist if one does not exist
                            if not changelist_num:
                                changelist_num = p4.create_changelist("Igby Redirector Cleaner")
                            
                            if changelist_num:
                                checked_out = p4.check_out_file(referencer_sys_path, changelist_num)
                            else:
                                logger.log_ue("Could not create a changelist.")

                            if checked_out:
                                logger.log_ue("Remapping!")
                                unreal.EditorAssetLibrary.load_asset(referencer_object_path)
                                unreal.EditorAssetLibrary.save_loaded_asset(referencer_asset, False)#save to fix hard references
                                fix_up_soft_object_paths(referencer_package, redirector_object, redirector_target_object)
                                unreal.EditorAssetLibrary.save_loaded_asset(referencer_asset, False)#save again after fixing soft references
                                asset_registry.scan_modified_asset_files([referencer_object.package_name])

                        except Exception as e:

                            if changelist_num in p4.get_client_changelists():
                                logger.log_ue("Error Detected! {}\nReverting Files and Deleting Changelist: {}".format(e, changelist_num), "error_clr")
                                p4.revert_changelist_files(changelist_num)
                                p4.delete_changelist(changelist_num)

                            #if something fails, revert files and delete CL.
                            error_message = traceback.format_exc()
                            raise Exception(error_message)

                    else:

                        file_owner = p4.get_file_owner(referencer_sys_path)
                        logger.log_ue("Warning! Perforce file {} is already checked out by: {}".format(referencer_sys_path, file_owner), "warning_clr")

                else:

                    logger.log_ue("File not in depot: {}".format(referencer_sys_path))

    logger.prefix = "    "
    logger.log_ue("")

    #check remaining redirectors to be deleted
    redirector_deleter_i.check()

    if len(redirector_deleter_i.redirectors_to_delete):

        if delete_redirectors:

            try:

                if not changelist_num:

                    changelist_num = p4.create_changelist("Igby Redirector Cleaner")

                redirector_deleter_i.delete(changelist_num)

            except Exception:

                if changelist_num in p4.get_client_changelists():
                    logger.log_ue("Error Detected! Reverting Files and Deleting Changelist: {}".format(changelist_num), "error_clr")
                    p4.revert_changelist_files(changelist_num)
                    p4.delete_changelist(changelist_num)

                #if something fails, revert files and delete CL.
                error_message = traceback.format_exc()
                raise Exception(error_message)

        else:

            redirector_deleter_i.list()

    #Sumbit changelist?
    if submit_changelist:
        logger.log_ue("Submitting Changelist: {}".format(changelist_num))
        p4.submit_changelist(changelist_num)

    return True


#this is a python implementation of function in UE5 codebase with the same name.
def fix_up_soft_object_paths(referencer_package, redirector_object, redirector_target_object):

    old_soft_path = str(ue_asset_lib.get_object_path(redirector_object))
    new_soft_path = str(ue_asset_lib.get_object_path(redirector_target_object))
    
    old_soft_object_path = unreal.SoftObjectPath(old_soft_path)
    new_soft_object_path = unreal.SoftObjectPath(new_soft_path)

    redirector_soft_path_map = unreal.Map(unreal.SoftObjectPath, unreal.SoftObjectPath)
    redirector_soft_path_map[old_soft_object_path] = new_soft_object_path

    if ue_asset_lib.get_asset_class(redirector_target_object) == 'Blueprint':

        old_soft_object_path_C = unreal.SoftObjectPath("{}_C".format(old_soft_path))
        new_soft_object_path_C = unreal.SoftObjectPath("{}_C".format(new_soft_path))
        redirector_soft_path_map[old_soft_object_path_C] = new_soft_object_path_C

        old_soft_object_path_Default_C = unreal.SoftObjectPath("{}.Default__{}_C".format(redirector_object.package_name, redirector_object.asset_name))
        new_soft_object_path_Default_C = unreal.SoftObjectPath("{}.Default__{}_C".format(redirector_target_object.package_name, redirector_target_object.asset_name))
        redirector_soft_path_map[old_soft_object_path_Default_C] = new_soft_object_path_Default_C

    unreal.AssetToolsHelpers.get_asset_tools().rename_referencing_soft_object_paths([referencer_package], redirector_soft_path_map)


#class that manages redirectors that should be deleted.
class redirector_deleter():

    redirectors_to_delete = set()
    redirectors_to_check = set()
    
    def __init__(self, p4, logger):
        self.logger = logger
        self.p4 = p4

    def add_to_delete(self, redirector_object):
        self.redirectors_to_delete.add(redirector_object)

    def add_to_check(self, redirector_object):
        self.redirectors_to_check.add(redirector_object)
 
    #Check if redirectors in redirectors_to_check set should be added to redirectors_to_delete set to later be deleted.
    def check(self):

        to_check_count = len(self.redirectors_to_check)

        if to_check_count > 0:

            self.logger.log_ue("Checking {} redirectors for possible deletion.\n".format(to_check_count))

            for redirector_object in self.redirectors_to_check:

                all_referencers = ue_asset_lib.get_connections(redirector_object, "referencers", True, True, True)

                if ue_asset_lib.class_only_test(all_referencers, "ObjectRedirector"):

                    self.add_to_delete(redirector_object)

                else:

                    all_dependencies = ue_asset_lib.get_connections(redirector_object, "dependencies", True, True, True)

                    if ue_asset_lib.class_only_test(all_dependencies, "ObjectRedirector"):

                        self.add_to_delete(redirector_object)


    def delete(self, changelist):

        to_delete_count = len(self.redirectors_to_delete)

        if to_delete_count > 0:

            self.logger.log_ue("Deleting {} unused redirectors:\n".format(to_delete_count))

            for redirector in self.redirectors_to_delete:

                redirector_object_path = ue_asset_lib.get_object_path(redirector)

                redirector_system_path = unreal.SystemLibrary.get_system_path(redirector.get_asset())

                if self.p4.is_file_available_for_checkout(redirector_system_path):

                    if self.p4.check_out_file(redirector_system_path, changelist):

                        if unreal.EditorAssetLibrary.delete_asset(redirector_object_path):

                            self.p4.move_to_changelist([redirector_system_path], changelist)
                            self.logger.log_ue("Deleted: {}".format(redirector_object_path))

                        else:

                            self.logger.log_ue("Warning! Redirector can't be deleted: {}".format(redirector_object_path), "warning_clr")
                    else:

                        self.logger.log_ue("Warning! Perforce file can't be checked out: {}".format(redirector_object_path), "warning_clr")

                else:

                    file_owner = self.p4.get_file_owner(redirector_system_path)
                    self.logger.log_ue("Warning! Perforce file {} is already checked out by: {}".format(redirector_object_path, file_owner), "warning_clr")


    def list(self):

        if len(self.redirectors_to_delete) > 0:

            self.logger.log_ue("The following redirectrors are unused and can be deleted:\n")

            for redirector in self.redirectors_to_delete:

                redirector_object_path = ue_asset_lib.get_object_path(redirector)
                self.logger.log_ue(redirector_object_path)