#blueprints_with_missing_parent_class_report_R.py for Igby UE Project Automator
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import os, unreal, igby_lib, ue_asset_lib

def run(settings, p4):
    
    #get setting
    paths_to_include = settings['PATHS_TO_INCLUDE']
    paths_to_ignore = settings['PATHS_TO_IGNORE']

    #setup logger
    logger = igby_lib.logger()
    logger.prefix = "    "

    logger.log_ue("Identifying blueprints that are missing a parent class.")
    logger.log_ue("")
    logger.log_ue("This is usually due to a parent class that has not been submitted or deleted.", "info_clr")
    logger.log_ue("These blueprints should be remapped to an existing class or removed to improve project integrity.", "info_clr")

    total_asset_count = 0

    filtered_assets = ue_asset_lib.get_assets(paths_to_include, paths_to_ignore, True)
    blueprint_assets = ue_asset_lib.filter_assets_of_class(filtered_assets, "Blueprint", "keep")

    blueprints_with_missing_parent_class = list()

    for blueprint in blueprint_assets:

        total_asset_count+=1

        bp_class_object_path = '{}_C'.format(blueprint.object_path)
        bp_gen_object = unreal.load_asset(bp_class_object_path)
        blueprint_class_default = unreal.get_default_object(bp_gen_object)

        if isinstance(blueprint_class_default, type(None)):

            system_path = unreal.SystemLibrary.get_system_path(blueprint.get_asset())
            user = p4.get_file_user(system_path)
            
            blueprints_with_missing_parent_class.append((user, blueprint.package_name))

    blueprints_with_missing_parent_class = sorted(blueprints_with_missing_parent_class)

    logger.log_ue("")
    logger.log_ue("Scanned {} blueprints.\n".format(total_asset_count))
    logger.log_ue("The following is a list of blueprints that are missing a parent class:\n")

    for blueprint in blueprints_with_missing_parent_class:

        logger.log_ue("{}, [{}]".format(blueprint[1], blueprint[0]))

    return True