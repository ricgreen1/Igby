# asset_source_availability_report_R.py for Igby UE Project Automator
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

from genericpath import isfile
import json, unreal, igby_lib, ue_asset_lib, module_settings

def run(settings_from_json, logger, p4):

    p4_root = p4.client_root.lower().replace("\\","/")

    #settings
    module_settings_definition = module_settings.report_module_base_settings_definition
    settings = igby_lib.validate_settings(settings_from_json, module_settings_definition, logger)

    #setup report
    report = igby_lib.report(settings, logger)
    report.set_log_message("The following is a list of all assets and their hard reference dependency info:\n")
    report.set_column_categories(["asset path", "source path", "asset class", "user", "date"])

    #description
    logger.log_ue("Identifying imported assets that do not have source files checked into Perforce.\n")

    #guidance
    logger.log_ue("Assets with missing source files can't be re-imported in the future.\nAll asset source files should be available in the Perforce Depot.\n", "info_clr")

    #logic
    filtered_assets = ue_asset_lib.get_assets(settings["PATHS_TO_INCLUDE"], settings["PATHS_TO_IGNORE"], True)

    progress_bar = igby_lib.long_process(len(filtered_assets), logger)

    asset_info = []

    for asset in filtered_assets:

        if not asset.is_redirector():
        
            asset_import_data = asset.get_tag_value('AssetImportData')

            if type(asset_import_data) is str and "RelativeFilename" in asset_import_data:
                
                if "\\" in asset_import_data:
                    asset_import_data = asset_import_data.replace("\\","/")
                
                asset_import_data_d = json.loads(asset_import_data)

                if type(asset_import_data_d) is list:

                    if len(asset_import_data_d) and type(asset_import_data_d[0]) is dict:

                        relative_path = asset_import_data_d[0]['RelativeFilename']

                        if relative_path.startswith('..'):
                            full_path = unreal.Paths.convert_relative_path_to_full(relative_path)
                        else:
                            full_path = relative_path

                        if not full_path.lower().startswith(p4_root) or not p4.is_file_in_depot(full_path):
                            package_name = asset.package_name
                            object_path = ue_asset_lib.get_object_path(asset)
                            asset_class = ue_asset_lib.get_asset_class(asset)
                            system_path = ue_asset_lib.get_package_system_path(package_name)
                            user = p4.get_file_user(system_path)
                            date = p4.get_file_date(system_path)
                            asset_info.append([object_path, full_path, asset_class, user, date])

        progress_bar.make_progress()

    logger.log_ue("Scanned {} assets.\n".format(len(filtered_assets)))

    #report
    for row in asset_info:

        report.add_row(row)

    report.output_report()

    return True