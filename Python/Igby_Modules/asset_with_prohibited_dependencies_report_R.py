# asset_with_prohibited_dependenices_report_R.py for Igby UE Project Automator
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import os, unreal, igby_lib, ue_asset_lib, module_settings

def run(settings_from_json, logger, p4):

    #settings
    module_specific_settings = list(module_settings.report_module_base_settings)
    module_specific_settings.append(["PROHIBITED_DEPENDENCY_PATHS"])
    settings = igby_lib.get_module_settings(settings_from_json, module_specific_settings, logger)

    #setup report
    report = igby_lib.report(settings["REPORT_SAVE_DIR"], settings["REPORT_TO_LOG"], logger)
    report.set_log_message("The following is a list of assets and their dependencies from prohibited paths:\n")
    report.set_column_categories(["asset", "prohibited dependency", "user"])

    #description
    logger.log_ue("Identifying packages that have dependencies from a prohibited path.\n")
    
    #guidance
    logger.log_ue("Prohibited dependencies should be fixed to ensure project indegrity.\n", "info_clr")

    #logic
    filtered_assets = ue_asset_lib.get_assets(settings["PATHS_TO_INCLUDE"], settings["PATHS_TO_IGNORE"], True)
    prohibited_assets = ue_asset_lib.get_assets(settings["PROHIBITED_DEPENDENCY_PATHS"], [], True)

    logger.log_ue("Analyzing {} assets.\n".format(len(filtered_assets)))

    prohibited_package_names = set()

    for prohibited_asset in prohibited_assets:

        prohibited_package_names.add(prohibited_asset.package_name)

    assets_with_prohibited_dependencies = {}

    for asset in filtered_assets:

        deps = ue_asset_lib.get_connections(asset, "dependencies", False, True, True)

        for dep in deps:
            
            if dep in prohibited_package_names:

                if asset.object_path in assets_with_prohibited_dependencies:
                    assets_with_prohibited_dependencies[asset.object_path][1].append(dep)
                else:
                    system_path = ue_asset_lib.get_package_system_path(asset.package_name)
                    user = p4.get_file_user(system_path)

                    assets_with_prohibited_dependencies[asset.object_path] = (user,[dep])

    logger.log_ue("Scanned {} assets.\n".format(len(filtered_assets)))

    #report
    for asset in assets_with_prohibited_dependencies:

        for prohibited_dep in assets_with_prohibited_dependencies[asset][1]:

            report.add_row([asset, prohibited_dep, assets_with_prohibited_dependencies[asset][0]])

    report.output_report()

    return True