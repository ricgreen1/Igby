# dual_asset_package_report_R.py for Igby UE Project Automator
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import igby_lib, ue_asset_lib, module_settings

def run(settings_from_json, logger, p4):

    #settings
    module_settings_definition = {}
    module_settings_definition.update(module_settings.content_path_base_settings_definition.copy())
    module_settings_definition.update(module_settings.report_module_base_settings_definition.copy())
    settings = igby_lib.validate_settings(settings_from_json, module_settings_definition, logger)

    #setup report
    report = igby_lib.report(settings, logger)
    report.set_log_message("The following Packages contains more than 1 Asset:\n")
    report.set_column_categories(["package", "asset count", "contains redirector", "user", "date"])
    
    #description
    logger.log_ue("Identifying packages that contain multiple assets.\n")

    #guidance
    logger.log_ue("It is best for assets to be in unique packages.\n", "info_clr")

    #logic
    packages_with_assets = {}

    filtered_assets = ue_asset_lib.get_assets(settings["PATHS_TO_INCLUDE"], settings["PATHS_TO_IGNORE"], True)

    progress_bar = igby_lib.long_process(len(filtered_assets), logger)

    for asset in filtered_assets:

        package_name = asset.package_name
        object_path = ue_asset_lib.get_object_path(asset)
        redirector = asset.is_redirector()

        if package_name in packages_with_assets:
            packages_with_assets[package_name].append([object_path, redirector])
        else:
            packages_with_assets[package_name] = [[object_path, redirector]]
        
        progress_bar.make_progress()

    #remove packages that contain all assets that are redirectors
    packages_with_multiple_assets = []
    for package_name in packages_with_assets:

        asset_count = len(packages_with_assets[package_name])

        if asset_count > 1:

            #if all redirector, then the multiple represents a bp that has been redirected.

            redirector = False

            for asset_info in packages_with_assets[package_name]:
                if asset_info[1]:
                    redirector = True
                    break

            system_path = ue_asset_lib.get_package_system_path(package_name)
            user = p4.get_file_user(system_path, "both")
            date = p4.get_file_date(system_path)

            packages_with_multiple_assets.append([package_name, asset_count, redirector, user, date])

    #report
    for row in packages_with_multiple_assets:
        report.add_row(row)

    logger.log_ue("Scanned {} assets.\n".format(len(filtered_assets)))

    report.output_report()

    return True