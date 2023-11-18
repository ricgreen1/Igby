# invalid_content_files_report_R.py for Igby UE Project Automator
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import os, unreal, igby_lib, ue_asset_lib, module_settings

def run(settings_from_json, logger, p4):

    #settings
    module_settings_definition = {}
    module_settings_definition.update(module_settings.content_path_base_settings_definition.copy())
    module_settings_definition.update(module_settings.report_module_base_settings_definition.copy())
    settings = igby_lib.validate_settings(settings_from_json, module_settings_definition, logger)

    #setup report
    report = igby_lib.report(settings, logger)
    report.set_log_message("The following is a list of all content files that are invalid and not recognized by UE:\n")
    report.set_column_categories(["invalid asset path", "user", "date"])

    #description
    logger.log_ue("Identifying invalid content files.\n")

    #guidance
    logger.log_ue("The invalid content files should be deleted as they are no longer evaluated by UE.\n", "info_clr")
 
    rel_content_path = unreal.Paths.project_content_dir()
    abs_content_path = unreal.Paths.convert_relative_path_to_full(rel_content_path).replace('/','\\')
    
    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    all_assets = asset_registry.get_assets_by_path("/Game", True, True)

    package_files = set()

    progress_bar = igby_lib.long_process(len(all_assets), logger)

    for asset in all_assets:

        if asset.asset_class_path.asset_name is not None:
            system_path = ue_asset_lib.get_package_system_path(asset.package_name)
            package_files.add(system_path.replace('/','\\'))

        progress_bar.make_progress()

    local_content_files = set()

    for r, d, f in os.walk(abs_content_path):
        for file in f:
            file_l = file.lower()
            if file_l.endswith(".uasset") or file_l.endswith(".umap"):
                local_content_files.add(os.path.join(r, file))

    invalid_package_files = list(local_content_files - package_files)
    invalid_package_files.sort()

    invalid_package_info = []
    
    for invalid_package_file in invalid_package_files:
        user = p4.get_file_user(invalid_package_file, "both")
        date = p4.get_file_date(invalid_package_file)
        invalid_package_info.append([invalid_package_file, user, date])

    logger.log_ue("Scanned {} assets.\n".format(len(all_assets)))

    #report
    for row in invalid_package_info:
        report.add_row(row)

    report.output_report()

    return True