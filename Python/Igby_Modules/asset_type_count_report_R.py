# asset_type_count_report_R.py for Igby UE Project Automator
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import os, unreal, igby_lib, ue_asset_lib

def run(settings):
    
    #get setting
    paths_to_include = settings['PATHS_TO_INCLUDE']
    paths_to_ignore = settings['PATHS_TO_IGNORE']

    #setup logger
    logger = igby_lib.logger()
    logger.prefix = "    "

    logger.log_ue("Getting asset types and their count.")
    logger.log_ue("This information can identify unknown asset usage as well as determine development focus.\n", "info_clr")

    total_asset_count = 0

    filtered_assets = ue_asset_lib.get_assets(paths_to_include, paths_to_ignore, True)

    asset_type_count = {}

    for asset in filtered_assets:

        total_asset_count+=1

        asset_class = asset.asset_class

        if asset.asset_class == "Blueprint":

            bp_class_object_path = '{}_C'.format(asset.object_path)
            bp_gen_object = unreal.load_asset(bp_class_object_path)
            blueprint_class_default = unreal.get_default_object(bp_gen_object)

            asset_class = "{} ({})".format(asset_class, type(blueprint_class_default).__name__)

        if asset_class in asset_type_count:
            
            asset_type_count[asset_class] += 1

        else:

            asset_type_count[asset_class] = 1

    asset_type_count = dict(reversed(sorted(asset_type_count.items(), key=lambda item: item[1])))

    logger.log_ue("Scanned {} assets.\n".format(total_asset_count))

    logger.log_ue("The following is a list of asset types and their count:\n")

    for asset_type in asset_type_count:

        logger.log_ue("{}, {}".format(asset_type_count[asset_type], asset_type))

    return True