# redirector_cleaner_S.py Module for Igby UE Project Automator
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import re
import unreal, traceback, igby_lib

def run(settings, p4):

    #get settings
    paths_to_monitor = settings['PATHS_TO_INCLUDE']
    paths_to_ignore = settings['PATHS_TO_IGNORE']
    delete_redirectors = settings['DELETE_REDIRECTORS'] #delete dangling redirectors? Make sure that they are not being accessed in code.
    submit_changelist = settings['SUBMIT_CHANGELIST'] #submit chcangelist? Do you feel lucky? or do you want to submit manually?

    #setup logger
    logger = igby_lib.logger()
    logger.prefix = "    "

    try:
        getattr(unreal, "EditorAssetLibrary")
    except:
        logger.log_ue("Error! Please enable the \"Editor Scripting Utilities\" plugin.", "error_clr")
        return False

    logger.log_ue("Remapping redirected assets.\n")

    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    dep_options = unreal.AssetRegistryDependencyOptions(include_soft_package_references=True, include_hard_package_references=True, include_searchable_names=False, include_soft_management_references=False, include_hard_management_references=False)

    changelist_num = 0

    redirector_deleter_i = redirector_deleter(p4, logger)
    
    for path_to_monitor in paths_to_monitor:
        #find all redirectors
        
        all_assets = asset_registry.get_assets_by_path(path_to_monitor, True)
        redirector_filter = unreal.ARFilter(class_names=["ObjectRedirector"])
        all_redirectors = asset_registry.run_assets_through_filter(all_assets, redirector_filter)

        all_filtered_redirectors = []

        #filter redirectors that are in paths_to_ignore or belong to package that has multiple assets.
        for redirector_object in all_redirectors:
            
            keep = True
            redirector_package_name = str(redirector_object.package_name)
            redirector_package_assets = asset_registry.get_assets_by_package_name(redirector_object.package_name)

            if len(redirector_package_assets) > 1:
                logger.log_ue("Warning: Skipping redirector because it's package contans multiple assets:", "warning_clr")
                logger.log_ue(redirector_package_assets, "warning_clr")
                continue

            for path_to_ignore in paths_to_ignore:
                if path_to_ignore.lower() in redirector_package_name.lower():
                    keep = False
                    break
            
            if keep:
                all_filtered_redirectors.append(redirector_object)

        logger.log_ue("Identified {} Redirectors:".format(len(all_filtered_redirectors)))

        #Loop through all appropriate redirectors
        for redirector_object in all_filtered_redirectors:

            redirector_package_name = str(redirector_object.package_name)
            redirector_object_path = str(redirector_object.object_path)
            
            logger.prefix = "    "
            logger.log_ue("")
            logger.log_ue("Processing Redirector: {}".format(redirector_object_path))
            logger.prefix = "      "

            all_dependencies = get_all_connections(redirector_object, "dependencies") 
            all_referencers = get_all_connections(redirector_object, "referencers") 

            if class_only_test(all_dependencies, "ObjectRedirector") or class_only_test(all_referencers, "ObjectRedirector"):

                redirector_deleter_i.add_to_delete(redirector_object)

            else:

                redirector_referencers = [*set(asset_registry.get_referencers(redirector_package_name, dep_options))]#this can be 0 or more assets. 0 means that that the redirector is not being used and can later be deleted.
                redirector_dependencies = asset_registry.get_dependencies(redirector_package_name, dep_options)#this should always be 0-1 assets. 0 assets means that the redirector is not valid and can later be deleted.

                #This accounts for situations where there is a redirector chain. This will find the asset that the chain is pointing at. If an asset is not found, then the redirector is marked for deletion.
                redirector_target_object = None

                while len(redirector_dependencies):

                    target_object = asset_registry.get_assets_by_package_name(redirector_dependencies[0])

                    if len(target_object) > 1:
                        logger.log_ue("Skipping redirector because it's dependency package ({}) contains more than 1 asset. Assets should be split up into individual packages.".format(redirector_dependencies[0]))
                        break
                    else:
                        target_object = target_object[0]

                    if target_object.asset_class == "ObjectRedirector":
                        target_package_name = str(target_object.package_name)
                        redirector_dependencies = asset_registry.get_dependencies(target_package_name, dep_options)
                    else:
                        redirector_target_object = target_object
                        break

                if redirector_target_object == None:
                    redirector_deleter_i.add_to_delete(redirector_object)
                    continue

                #Later we will determine which of these redirectors can be deleted.
                redirector_deleter_i.add_to_check(redirector_object)

                #Now that we have all the necessary elements, we will go ahead and clean up redirectors.
                for redirector_referencer in redirector_referencers:

                    referencer_object = asset_registry.get_assets_by_package_name(redirector_referencer)

                    if len(referencer_object) > 1:
                        logger.log_ue("Skipping redirector because it's referencer package ({}) contains more than 1 asset. Assets should be split up into individual packages.".format(referencer_object,))
                        break
                    else:
                        referencer_object = referencer_object[0]

                    #check if this asset is a redirector. Skip because this redirector should already be in the "all_filtered_redirectors" list.
                    if referencer_object.asset_class == "ObjectRedirector":
                        logger.log_ue("Skipping redirector because it's referencer is a redirector.")
                        continue

                    referencer_object_path = referencer_object.object_path

                    #check if referencer asset is in path_to_ignore
                    skip = False
                    for path_to_ignore in paths_to_ignore:
                        if path_to_ignore.lower() in str(referencer_object_path).lower():
                            skip = True
                            break

                    if skip:
                        logger.log_ue("Skipping redirector because it's referencer is in a \"paths_to_ignore\" path: {}".format(referencer_object.object_path))
                        continue

                    #connect referencer to target to avoid redirector.
                    logger.log_ue("")
                    logger.log_ue("Redirector Referencer: {}".format(redirector_referencer))

                    referencer_asset = referencer_object.get_asset()
                    referencer_sys_path = unreal.SystemLibrary.get_system_path(referencer_asset)
                    referencer_package = unreal.find_package(referencer_object.package_name)

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

                            except Exception:

                                if changelist_num in p4.get_client_changelists():
                                    logger.log_ue("Error Detected! Reverting Files and Deleting Changelist: {}".format(changelist_num), "error_clr")
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

def get_all_connections(object, type = "referencers"):

    if type == "dependencies" or type == "referencers":

        asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
        dep_options = unreal.AssetRegistryDependencyOptions(include_soft_package_references=True, include_hard_package_references=True, include_searchable_names=False, include_soft_management_references=False, include_hard_management_references=False)

        object_package_name = object.package_name
        package_names = [object_package_name]
        all_connections = set()

        all_connections_len_start = -1
        all_connections_len_end = 0

        while all_connections_len_start < all_connections_len_end:

            all_connections_len_start = len(all_connections)
            package_names_new = set()

            for package_name in package_names:

                if type == "referencers":
                    connections = set(asset_registry.get_referencers(package_name, dep_options))
                elif type == "dependencies":
                    connections = set(asset_registry.get_dependencies(package_name, dep_options))

                all_connections = all_connections | connections
                package_names_new = package_names_new | connections
            
            package_names = package_names_new
            all_connections_len_end = len(all_connections)

        all_connections = all_connections - set([object_package_name])

        return list(all_connections)
  
    else:

        raise Exception("2nd argument should be either \"referencers\" or \"dependencies\"")


def class_only_test(package_names, class_name):

    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    class_only = True

    for package_name in package_names:

        assets = asset_registry.get_assets_by_package_name(package_name)

        for asset in assets:

            if asset.asset_class != class_name:
                class_only = False
                break
        
        if not class_only:
            break

    return class_only


#this is a python implementation of function in UE5 codebase with the same name.
def fix_up_soft_object_paths(referencer_package, redirector_object, redirector_target_object):

    old_soft_path = str(redirector_object.object_path)
    new_soft_path = str(redirector_target_object.object_path)
    
    old_soft_object_path = unreal.SoftObjectPath(old_soft_path)
    new_soft_object_path = unreal.SoftObjectPath(new_soft_path)

    redirector_soft_path_map = unreal.Map(unreal.SoftObjectPath, unreal.SoftObjectPath)
    redirector_soft_path_map[old_soft_object_path] = new_soft_object_path

    if redirector_target_object.asset_class == 'Blueprint':

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

                all_dependencies = get_all_connections(redirector_object, "dependencies")

                if class_only_test(all_dependencies, "ObjectRedirector"):

                    self.add_to_delete(redirector_object)

                else:

                    all_referencers = get_all_connections(redirector_object, "referencers")

                    if class_only_test(all_referencers, "ObjectRedirector"):

                        self.add_to_delete(redirector_object)


    def delete(self, changelist):

        to_delete_count = len(self.redirectors_to_delete)

        if to_delete_count > 0:

            self.logger.log_ue("Deleting {} unused redirectors:\n".format(to_delete_count))

            for redirector in self.redirectors_to_delete:

                redirector_object_path = redirector.object_path

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

                redirector_object_path = redirector.object_path
                self.logger.log_ue(redirector_object_path)