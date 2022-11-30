# invalid_content_files_report_R.py for Igby UE Project Automator
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

from genericpath import isfile
import os, json, unreal, igby_lib, ue_asset_lib, module_settings

def run(settings_from_json, logger, p4):

    #settings
    module_specific_settings = list(module_settings.report_module_base_settings)
    settings = igby_lib.get_module_settings(settings_from_json, module_specific_settings, logger)

    #setup report
    report = igby_lib.report(settings["REPORT_SAVE_DIR"], settings["REPORT_TO_LOG"], logger)
    report.set_log_message("The following is a list of all content files that are invalid and not recognized by UE:\n")
    report.set_column_categories(["invalid asset path"])

    #description
    logger.log_ue("Identifying invalid content files.\n")

    #guidance
    logger.log_ue("The invalid content files should be deleted as they are no longer evaluated by UE.\n", "info_clr")
 
    rel_content_path = unreal.Paths.project_content_dir()
    abs_content_path = unreal.Paths.convert_relative_path_to_full(rel_content_path).replace('/','\\')

    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    all_assets = asset_registry.get_assets_by_path("/Game", True, True)

    package_files = set()

    for asset in all_assets:

        system_path = ue_asset_lib.get_package_system_path(asset.package_name)
        package_files.add(system_path.replace('/','\\'))

    local_content_files = set()

    for r, d, f in os.walk(abs_content_path):
        for file in f:
            if file.lower().endswith(".uasset") or file.lower().endswith(".umap"):
                local_content_files.add(os.path.join(r, file))

    invalid_package_files = list(local_content_files - package_files)

    logger.log_ue("Scanned {} assets.\n".format(len(all_assets)))

    for invalid_package_file in invalid_package_files:

        report.add_row([invalid_package_file])

    report.output_report()

    return True