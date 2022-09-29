# dual_asset_package_report_R.py for Igby UE Project Automator
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import unreal, igby_lib, ue_asset_lib

def run(settings):
    
    #get settings
    paths_to_include = settings['PATHS_TO_INCLUDE']
    paths_to_ignore = settings['PATHS_TO_IGNORE']

    #setup logger
    logger = igby_lib.logger()
    logger.prefix = "    "

    logger.log_ue("Identifying packages that contain multiple assets.\n")
    logger.log_ue("It is best for assets to be in individual packages.\n")

    packages_with_assets = {}

    filtered_assets = ue_asset_lib.get_assets(paths_to_include, paths_to_ignore, True)

    for asset in filtered_assets:

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