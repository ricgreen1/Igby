# dual_asset_package_report_R.py for Igby UE Project Automator
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import unreal, igby_lib

def run(settings, p4):
    
    #get settings
    paths_to_monitor = tuple(settings['PATHS_TO_INCLUDE'])
    paths_to_ignore = tuple(settings['PATHS_TO_IGNORE'])

    #setup logger
    logger = igby_lib.logger()
    logger.prefix = "    "

    logger.log_ue("Identifying packages that contain multiple assets.\n")

    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()

    packages_with_assets = {}

    for path_to_monitor in paths_to_monitor:

        all_assets = asset_registry.get_assets_by_path(path_to_monitor, True)

        for asset in all_assets:

            skip = False

            for path_to_ignore in paths_to_ignore:
                if path_to_ignore.lower() in str(asset.object_path).lower():
                    skip = True
                    break

            if skip:
                continue

            package_name = asset.package_name

            if package_name in packages_with_assets:
                packages_with_assets[package_name].append(asset.object_path)
            else:
                packages_with_assets[package_name] = [asset.object_path]

    logger.log_ue("Scanned {} packages.\n".format(len(packages_with_assets)))

    issue_found = False

    for package in packages_with_assets:

        if len(packages_with_assets[package_name]) > 1:

            issue_found = True

            logger.prefix = "    "
            logger.log_ue("")
            logger.log_ue("The following Package contains more than 1 Asset: {}".format(package))
            logger.prefix = "      "

            for asset in packages_with_assets[package_name]:
                logger.log_ue(asset.object_path)

    if not issue_found:
        logger.log_ue("No issues found.")



    
    return True