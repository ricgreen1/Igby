# dual_asset_package_report_R.py for Igby UE Project Automator
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import unreal, igby_lib, ue_asset_lib, module_settings

def run(settings_from_json, logger, p4):

    #settings
    module_specific_settings = list(module_settings.report_module_base_settings)
    settings = igby_lib.get_module_settings(settings_from_json, module_specific_settings, logger)

    #setup report
    report = igby_lib.report(settings["REPORT_SAVE_DIR"], settings["REPORT_TO_LOG"], logger)
    report.set_log_message("The following Packages contains more than 1 Asset:\n")
    report.set_column_categories(["package", "asset", "user"])
    
    #description
    logger.log_ue("Identifying packages that contain multiple assets.\n")

    #guidance
    logger.log_ue("It is best for assets to be in unique packages.\n", "info_clr")

    #logic
    packages_with_assets = {}

    filtered_assets = ue_asset_lib.get_assets(settings["PATHS_TO_INCLUDE"], settings["PATHS_TO_IGNORE"], True)

    for asset in filtered_assets:

        package_name = asset.package_name
        object_path = ue_asset_lib.get_object_path(asset)

        if package_name in packages_with_assets:

            if(packages_with_assets[package_name][0] == ""):
                system_path = ue_asset_lib.get_package_system_path(asset.package_name)
                user = p4.get_file_user(system_path)
                packages_with_assets[package_name][0] = user

            packages_with_assets[package_name][1].append(object_path)
        else:
            packages_with_assets[package_name] = ["",[object_path]]

    logger.log_ue("Scanned {} packages.\n".format(len(packages_with_assets)))

    #report
    for package in packages_with_assets:

        if len(packages_with_assets[package][1]) > 1:

            for asset_object_path in packages_with_assets[package][1]:
                report.add_row([package, asset_object_path, packages_with_assets[package][0]])

    report.output_report()

    return True