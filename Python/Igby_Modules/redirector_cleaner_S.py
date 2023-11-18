# redirector_cleaner_S.py Module for Igby UE Project Automator
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import unreal, traceback, ue_asset_lib, igby_lib, module_settings

def run(settings_from_json, logger, p4):

    #get settings
    module_settings_definition = {}
    module_settings_definition.update({"DELETE_REDIRECTORS":{"type":"bool", "default":False, "info":"Delete unused redirectors? Make sure that they are not being accessed in code."}})
    module_settings_definition.update({"SUBMIT_CHANGELIST":{"type":"bool", "default":False, "info":"Automatically submit resulting changelist?"}})
    module_settings_definition.update(module_settings.content_path_base_settings_definition.copy())
    settings = igby_lib.validate_settings(settings_from_json, module_settings_definition, logger)

    paths_to_monitor = settings['PATHS_TO_INCLUDE']
    paths_to_ignore = settings['PATHS_TO_IGNORE']
    delete_redirectors = settings['DELETE_REDIRECTORS'] 
    submit_changelist = settings['SUBMIT_CHANGELIST']

    logger.log("Remapping redirected assets.\n")

    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    dep_options_hard = unreal.AssetRegistryDependencyOptions(include_soft_package_references=False, include_hard_package_references=True, include_searchable_names=False, include_soft_management_references=False, include_hard_management_references=False)
    dep_options_soft = unreal.AssetRegistryDependencyOptions(include_soft_package_references=True, include_hard_package_references=False, include_searchable_names=False, include_soft_management_references=False, include_hard_management_references=False)
    dep_options = unreal.AssetRegistryDependencyOptions(include_soft_package_references=True, include_hard_package_references=True, include_searchable_names=False, include_soft_management_references=False, include_hard_management_references=False)
    all_assets = ue_asset_lib.get_assets(paths_to_monitor, paths_to_ignore, False, False)
    redirector_class_path = unreal.TopLevelAssetPath(package_name = "/Script/CoreUObject", asset_name="ObjectRedirector")
    redirector_filter = unreal.ARFilter(class_paths=[redirector_class_path])
    all_redirectors = asset_registry.run_assets_through_filter(all_assets, redirector_filter)

    redirector_deleter_i = redirector_deleter(p4, logger)
    changelist_num = 0

    #find all redirectors
    
    all_filtered_redirector_packages = set()

    #filter redirectors that belong to package that contain non redirector assets.
    for redirector_object in all_redirectors:
        
        redirector_package_name = str(redirector_object.package_name)
        redirector_assets = asset_registry.get_assets_by_package_name(redirector_package_name)
        if len(redirector_assets) > 1:
            logger.log(f"Skipping redirector because package has more than one asset: {redirector_package_name}.{redirector_object.asset_name}")
            continue

        all_filtered_redirector_packages.add(redirector_package_name)

    logger.log(f"Identified {len(all_filtered_redirector_packages)} Redirectors:")

    saved_files = []
    checked_out_files = []

    #Loop through all appropriate redirectors
    for redirector_package_name in all_filtered_redirector_packages:

        to_check = True

        logger.prefix = "    "
        logger.log("")
        logger.log(f"Processing Redirector: {redirector_package_name}")
        logger.prefix = "      "

        all_dependencies = ue_asset_lib.get_package_connections(redirector_package_name, "dependencies", True, True, True) 
        all_referencers = ue_asset_lib.get_package_connections(redirector_package_name, "referencers", True, True, True) 

        if ue_asset_lib.class_only_test(all_dependencies, "ObjectRedirector") or ue_asset_lib.class_only_test(all_referencers, "ObjectRedirector"):

            redirector_deleter_i.add_to_delete(redirector_package_name)
            logger.log("To be deleted.")

        else:

            #get nearest dependencies
            redirector_referencers = [*set(asset_registry.get_referencers(redirector_package_name, dep_options))]#this can be 0 or more assets. 0 means that that the redirector is not being used and can later be deleted.
            redirector_dependencies = asset_registry.get_dependencies(redirector_package_name, dep_options)#this should always be 0-1 assets. 0 assets means that the redirector is not valid and can later be deleted.

            if len(redirector_referencers) == 0 or len(redirector_dependencies) == 0:
                redirector_deleter_i.add_to_delete(redirector_package_name)
                continue

            if len(redirector_dependencies) > 1:
                logger.log(f"Skipping redirector because it has more than 1 target package: {len(redirector_dependencies)}", "warning_clr")
                continue
            
            #Fix hard references (This is most of the references)
            hard_redirector_referencers = [*set(asset_registry.get_referencers(redirector_package_name, dep_options_hard))]

            if len(hard_redirector_referencers) > 0:
                logger.log("Fixing Hard References.")

                #Now that we have all the necessary elements, we will go ahead and clean up hard redirectors.
                for redirector_referencer in hard_redirector_referencers:

                    saved = False
                    checked_out = False

                    #connect referencer to target to avoid redirector.
                    logger.log(f"Redirector Referencer: {redirector_referencer}")

                    referencer_sys_path = ue_asset_lib.get_package_system_path(redirector_referencer)

                    if referencer_sys_path in saved_files:
                        logger.log(f"Referencer already fixed up: {redirector_referencer}")
                        continue
                    
                    if referencer_sys_path not in checked_out_files:

                        checked_out_info = check_out_helper(p4, logger, referencer_sys_path, changelist_num)
                        checked_out = checked_out_info[0]
                        changelist_num = checked_out_info[1]

                        if checked_out:
                            checked_out_files.append(referencer_sys_path)

                    try:
                        
                        if checked_out:

                            logger.log("Remapping!")
                            loaded_package = unreal.load_package(redirector_referencer)
                            saved = unreal.EditorLoadingAndSavingUtils.save_packages([loaded_package],False)

                            if saved:
                                saved_files.append(referencer_sys_path)
                                asset_registry.scan_modified_asset_files([redirector_referencer])
                            else:
                                logger.log(f"Could not save referencer: {referencer_sys_path}", "warning_clr")

                        if not saved:
                            to_check = False

                    except Exception as e:
                        
                        #if something fails, revert files and delete CL.
                        if changelist_num in p4.get_client_changelists():
                            logger.log(f"Error Detected! {e}\nReverting Files and Deleting Changelist: {changelist_num}", "error_clr")
                            p4.revert_changelist_files(changelist_num)
                            p4.delete_changelist(changelist_num)

                        error_message = traceback.format_exc()
                        logger.log(e, "error_clr")
                        logger.log(error_message, "error_clr")
                        raise Exception(error_message)

    
            #Fix soft references (This is most of the references)
            soft_redirector_referencers = [*set(asset_registry.get_referencers(redirector_package_name, dep_options_soft))]

            if len(soft_redirector_referencers) > 0:

                logger.log("Fixing Soft References.")

                #Now that we have all the necessary elements, we will go ahead and clean up soft redirectors.
                for redirector_referencer in soft_redirector_referencers:

                    saved = False
                    checked_out = False

                    #connect referencer to target to avoid redirector.
                    logger.log(f"Redirector Referencer: {redirector_referencer}")

                    referencer_sys_path = ue_asset_lib.get_package_system_path(redirector_referencer)

                    if referencer_sys_path not in checked_out_files:

                        checked_out_info = check_out_helper(p4, logger, referencer_sys_path, changelist_num)
                        checked_out = checked_out_info[0]
                        changelist_num = checked_out_info[1]

                        if checked_out:
                            checked_out_files.append(referencer_sys_path)
                    else:

                        checked_out = True

                    #find redirector object
                    redirector_asset = None
                    redirector_assets = asset_registry.get_assets_by_package_name(redirector_package_name)
                    for redirector_asset in redirector_assets:
                        if str(redirector_asset.asset_name).endswith("_C"):
                            continue
                        else:
                            break

                    #find redirector target object
                    redirector_target_asset = None
                    target_package_name = redirector_package_name

                    while redirector_target_asset == None or redirector_target_asset.asset_class_path.asset_name == "ObjectRedirector":
                        redirector_dependencies_soft = asset_registry.get_dependencies(target_package_name, dep_options)

                        if len(redirector_dependencies_soft):

                            for redirector_target_package in redirector_dependencies_soft:

                                redirector_target_assets = asset_registry.get_assets_by_package_name(redirector_target_package)

                                for redirector_target_asset in redirector_target_assets:

                                    if str(redirector_asset.asset_name).endswith("_C"):
                                        continue
                                    else:
                                        break
                        
                        target_package_name = redirector_target_asset.package_name

                    try:
                        
                        if checked_out:

                            logger.log("Remapping!")
                            loaded_package = unreal.load_package(redirector_referencer)
                            fix_up_soft_object_path(logger, loaded_package, redirector_asset, redirector_target_asset)
                            saved = unreal.EditorLoadingAndSavingUtils.save_packages([loaded_package],False)

                            if saved:
                                asset_registry.scan_modified_asset_files([redirector_referencer])
                            else:
                                logger.log(f"Could not save referencer: {referencer_sys_path}", "warning_clr")

                        if not saved:
                            to_check = False

                    except Exception as e:
                        
                        #if something fails, revert files and delete CL.
                        if changelist_num in p4.get_client_changelists():
                            logger.log(f"Error Detected! {e}\nReverting Files and Deleting Changelist: {changelist_num}", "error_clr")
                            p4.revert_changelist_files(changelist_num)
                            p4.delete_changelist(changelist_num)

                        error_message = traceback.format_exc()
                        logger.log(e, "error_clr")
                        logger.log(error_message, "error_clr")
                        raise Exception(error_message)

            if to_check:
                redirector_deleter_i.add_to_check(redirector_package_name)
                logger.log("Marked to be checked for deletion.")

    logger.prefix = "    "
    logger.log("")

    #check remaining redirectors to be deleted
    redirector_deleter_i.check()

    if len(redirector_deleter_i.redirectors_to_delete):

        if delete_redirectors:

            try:

                changelist_num = redirector_deleter_i.delete(changelist_num)

            except Exception as e:

                if changelist_num in p4.get_client_changelists():
                    logger.log(f"Error Detected! Reverting Files and Deleting Changelist: {changelist_num}", "error_clr")
                    p4.revert_changelist_files(changelist_num)
                    p4.delete_changelist(changelist_num)

                #if something fails, revert files and delete CL.
                error_message = traceback.format_exc()
                logger.log(e, "error_clr")
                logger.log(error_message, "error_clr")
                raise Exception(error_message)

        else:

            redirector_deleter_i.log_redirectors()

    #Sumbit changelist?
    if submit_changelist and changelist_num != 0:
        logger.log(f"Submitting Changelist: {changelist_num}")
        p4.submit_changelist(changelist_num)

    return True


#this is a python implementation of function in UE5 codebase with the same name.
def fix_up_soft_object_path(logger, referencer_package, redirector_object, redirector_target_object):

    old_soft_path = str(ue_asset_lib.get_object_path(redirector_object))
    new_soft_path = str(ue_asset_lib.get_object_path(redirector_target_object))
    
    old_soft_object_path = unreal.SoftObjectPath(old_soft_path)
    new_soft_object_path = unreal.SoftObjectPath(new_soft_path)

    redirector_soft_path_map = unreal.Map(unreal.SoftObjectPath, unreal.SoftObjectPath)
    redirector_soft_path_map[old_soft_object_path] = new_soft_object_path

    target_class = ue_asset_lib.get_asset_class(redirector_target_object)
    logger.log(target_class)

    old_path_C = f"{old_soft_path}_C"
    new_path_C = f"{new_soft_path}_C"
    old_soft_object_path_C = unreal.SoftObjectPath(old_path_C)
    new_soft_object_path_C = unreal.SoftObjectPath(new_path_C)
    redirector_soft_path_map[old_soft_object_path_C] = new_soft_object_path_C

    old_path_Default_C = f"{redirector_object.package_name}.Default__{redirector_object.asset_name}_C"
    new_path_Default_C = f"{redirector_target_object.package_name}.Default__{redirector_target_object.asset_name}_C"
    old_soft_object_path_Default_C = unreal.SoftObjectPath(old_path_Default_C)
    new_soft_object_path_Default_C = unreal.SoftObjectPath(new_path_Default_C)
    redirector_soft_path_map[old_soft_object_path_Default_C] = new_soft_object_path_Default_C

    unreal.AssetToolsHelpers.get_asset_tools().rename_referencing_soft_object_paths([referencer_package], redirector_soft_path_map)

def check_out_helper(p4, logger, file, changelist_num):
    
    checked_out = False

    if p4.is_file_in_depot(file):

        if p4.is_file_available_for_checkout(file):

                #create changelist if one does not exist
                if not changelist_num:
                    changelist_num = p4.create_changelist("Igby Redirector Cleaner")
                
                if changelist_num:
                    checked_out = p4.check_out_file(file, changelist_num)

                else:
                    logger.log("Could not create a changelist.", "warning_clr")
        
        else:

            file_owner = p4.get_file_owner(file)
            logger.log(f"Warning! Perforce file {file} is already checked out by: {file_owner}", "warning_clr")
    else:

        logger.log(f"File not in depot: {file}", "warning_clr")

    return [checked_out, changelist_num]

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

            self.logger.log(f"Checking {to_check_count} redirectors for possible deletion.\n")

            for redirector_object in self.redirectors_to_check:

                all_referencers = ue_asset_lib.get_package_connections(redirector_object, "referencers", True, True, True)

                soft_referencers = ue_asset_lib.get_package_connections(redirector_object, "referencers", True, False, False)
                for soft in soft_referencers:
                    self.logger.log(f"softR:{soft}")
                hard_referencers = ue_asset_lib.get_package_connections(redirector_object, "referencers", False, True, False)
                for hard in hard_referencers:
                    self.logger.log(f"hardR:{hard}")

                if len(all_referencers) == 0 or ue_asset_lib.class_only_test(all_referencers, "ObjectRedirector"):

                    self.add_to_delete(redirector_object)

                else:

                    self.logger.log(f"Redirector still has referencers: {redirector_object}")

                    all_dependencies = ue_asset_lib.get_package_connections(redirector_object, "dependencies", True, True, True)

                    soft_dependencies = ue_asset_lib.get_package_connections(redirector_object, "dependencies", True, False, False)
                    for soft in soft_dependencies:
                        self.logger.log(f"softD:{soft}")
                    hard_dependencies = ue_asset_lib.get_package_connections(redirector_object, "dependencies", False, True, False)
                    for hard in hard_dependencies:
                        self.logger.log(f"hardD:{hard}")

                    if len(all_dependencies) == 0 or ue_asset_lib.class_only_test(all_dependencies, "ObjectRedirector"):

                        self.logger.lg(f"Marking redirector for deletion: {redirector_object}")
                        self.add_to_delete(redirector_object)
                    else:
                        self.logger.log(f"Redirector still has dependencies: {redirector_object}")


    def delete(self, changelist_num):

        to_delete_count = len(self.redirectors_to_delete)

        if to_delete_count > 0:

            self.logger.log(f"Deleting {to_delete_count} unused redirectors:\n")

            for redirector in self.redirectors_to_delete:

                redirector_system_path = ue_asset_lib.get_package_system_path(redirector)
                # loaded_package = unreal.load_package(redirector)
                # unreal.EditorLoadingAndSavingUtils.unload_packages([loaded_package])
                
                if self.p4.is_file_available_for_checkout(redirector_system_path):

                    if not changelist_num:

                        changelist_num = self.p4.create_changelist("Igby Redirector Cleaner")

                    if self.p4.mark_for_delete(redirector_system_path, changelist_num):

                        self.logger.log(f"Deleted: {redirector_system_path}")

                    else:

                        self.logger.log(f"Warning! Redirector can't be deleted: {redirector_system_path}", "warning_clr")

                else:

                    file_owner = self.p4.get_file_owner(redirector_system_path)
                    self.logger.log(f"Warning! Perforce file {redirector_system_path} is already checked out by: {file_owner}", "warning_clr")

        return changelist_num


    def log_redirectors(self):

        if len(self.redirectors_to_delete) > 0:

            self.logger.log("The following redirectrors are unused and can be deleted:\n")

            for redirector in self.redirectors_to_delete:
                self.logger.log(redirector)