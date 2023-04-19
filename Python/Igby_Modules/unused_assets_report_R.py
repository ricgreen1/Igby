# unused_assets_report_R.py for Igby UE Project Automator
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import igby_lib, ue_asset_lib, module_settings

def run(settings_from_json, logger, p4):

    #settings
    module_settings_definition = module_settings.report_module_base_settings_definition
    settings = igby_lib.validate_settings(settings_from_json, module_settings_definition, logger)

    #setup report
    report = igby_lib.report(settings, logger)
    report.set_log_message("The following is a list of packages that are unused:\n")
    report.set_column_categories(["package_name", "asset type", "user", "date"])

    #description
    logger.log_ue("Identifying packages that are unused.\n")

    #guidance
    logger.log_ue("You should consider cleaning these packages out to clean up the project.", "info_clr")
    logger.log_ue("Be aware that this report tests package to package referencing only.", "info_clr")
    logger.log_ue("Some of these packages may still be used without being referenced by other packages.", "info_clr")
    logger.log_ue("Please be mindful when removing these assets from the project.\n", "info_clr")

    #logic
    total_asset_count = 0

    filtered_assets = ue_asset_lib.get_assets(settings["PATHS_TO_INCLUDE"], settings["PATHS_TO_IGNORE"], True)

    unused_assets = list()

    progress_bar = igby_lib.long_process(len(filtered_assets), logger)

    for asset in filtered_assets:

        total_asset_count+=1

        deps = ue_asset_lib.get_connections(asset, "referencers", True, True, False)

        if len(deps) == 0:

            package_name = asset.package_name
            package_system_path = ue_asset_lib.get_package_system_path(package_name)
            asset_class = ue_asset_lib.get_asset_class(asset)
            user = p4.get_file_user(package_system_path)
            date = p4.get_file_date(package_system_path)

            unused_assets.append([package_name, asset_class, user, date])

        progress_bar.make_progress()

    logger.log_ue("")
    logger.log_ue("Scanned {} assets.\n".format(total_asset_count))

    unused_assets = sorted(unused_assets)

    #report
    for row in unused_assets:
        report.add_row(row)

    report.output_report()

    return True