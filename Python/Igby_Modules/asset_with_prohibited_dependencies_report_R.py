# asset_with_prohibited_dependenices_report_R.py for Igby UE Project Automator
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import igby_lib, ue_asset_lib, module_settings

def run(settings_from_json, logger, p4):

    #settings
    module_settings_definition = module_settings.report_module_base_settings_definition
    module_settings_definition.update({"PROHIBITED_DEPENDENCY_PATHS":{"type":"list(str)", "info":"Content folders that contain assets which should be prohibited from project assets."}})
    settings = igby_lib.validate_settings(settings_from_json, module_settings_definition, logger)

    #setup report
    report = igby_lib.report(settings, logger)
    report.set_log_message("The following is a list of assets and their dependencies from prohibited paths:\n")
    report.set_column_categories(["asset", "prohibited dependency", "user", "date"])

    #description
    logger.log_ue("Identifying packages that have dependencies from a prohibited path.\n")
    
    #guidance
    logger.log_ue("Prohibited dependencies should be fixed to ensure project integrity.\n", "info_clr")

    #logic
    filtered_assets = ue_asset_lib.get_assets(settings["PATHS_TO_INCLUDE"], settings["PATHS_TO_IGNORE"], True)
    prohibited_assets = ue_asset_lib.get_assets(settings["PROHIBITED_DEPENDENCY_PATHS"], [], True)

    progress_bar = igby_lib.long_process(len(filtered_assets), logger)

    prohibited_package_names = set()

    for prohibited_asset in prohibited_assets:

        prohibited_package_names.add(prohibited_asset.package_name)

    assets_with_prohibited_dependencies = []

    for asset in filtered_assets:

        deps = set(ue_asset_lib.get_connections(asset, "dependencies", True, True, False))

        prohibited_deps = deps.intersection(prohibited_package_names)

        if len(prohibited_deps) > 0:

            system_path = ue_asset_lib.get_package_system_path(asset.package_name)
            user = p4.get_file_user(system_path)
            date = p4.get_file_date(system_path)
            object_path = ue_asset_lib.get_object_path(asset)

            for dep in prohibited_deps:

                assets_with_prohibited_dependencies.append([object_path, dep, user, date])

        progress_bar.make_progress()

    logger.log_ue("Scanned {} assets.\n".format(len(filtered_assets)))

    #report
    for row in assets_with_prohibited_dependencies:

        report.add_row(row)

    report.output_report()

    return True