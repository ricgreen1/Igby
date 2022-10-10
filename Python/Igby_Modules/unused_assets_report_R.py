# unused_assets_report_R.py for Igby UE Project Automator
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

    logger.log_ue("Identifying packages that are unused.")
    logger.log_ue("")
    logger.log_ue("You should consider cleaning these packages out to clean up the project.", "info_clr")
    logger.log_ue("Be aware that this report tests package to package referencing only.", "info_clr")
    logger.log_ue("Some of these packages may still be used without being referenced by other packages.", "info_clr")
    logger.log_ue("Please be mindful when removing these assets from the project.", "info_clr")

    total_asset_count = 0

    filtered_assets = ue_asset_lib.get_assets(paths_to_include, paths_to_ignore, True)

    unused_assets = set()

    for asset in filtered_assets:

        total_asset_count+=1

        deps = ue_asset_lib.get_connections(asset, "referencers", True, True, False)

        if len(deps) == 0:

            system_path = unreal.SystemLibrary.get_system_path(asset.get_asset())
            user = p4.get_file_user(system_path)

            unused_assets.add((asset.asset_class, asset.package_name, user))

    logger.log_ue("")
    logger.log_ue("Scanned {} assets.\n".format(total_asset_count))

    logger.log_ue("The following is a list of packages that are unused:\n")

    unused_assets = sorted(unused_assets)

    for unused_asset in unused_assets:

        logger.log_ue("{}, {}, [{}]".format(unused_asset[0], unused_asset[1], unused_asset[2]))

    return True