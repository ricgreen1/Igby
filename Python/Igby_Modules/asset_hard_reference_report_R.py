# asset_hard_reference_report_R.py for Igby UE Project Automator
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import os, igby_lib, ue_asset_lib, module_settings

def run(settings_from_json, logger, p4):

    #settings
    module_settings_definition = {}
    module_settings_definition.update(module_settings.content_path_base_settings_definition.copy())
    module_settings_definition.update(module_settings.report_module_base_settings_definition.copy())
    settings = igby_lib.validate_settings(settings_from_json, module_settings_definition, logger)

    #setup report
    report = igby_lib.report(settings, logger)
    report.set_log_message("The following is a list of all assets and their hard reference dependency info:\n")
    report.set_column_categories(["disk size Mb", "hard reference count", "asset class", "package name", "user", "date"])

    #description
    logger.log_ue("Identifying packages that have a large hard reference chain.\n")

    #guidance
    logger.log_ue("To reduce the hard reference chain size, remove hard references or replace them with soft references.\n", "info_clr")

    #logic
    asset_memory_lookup = dict()
    asset_hard_ref_mem = list()

    filtered_assets = ue_asset_lib.get_assets(settings["PATHS_TO_INCLUDE"], settings["PATHS_TO_IGNORE"], True)

    progress_bar = igby_lib.long_process(len(filtered_assets), logger)

    for asset in filtered_assets:

        deps = ue_asset_lib.get_connections(asset, "dependencies", False, True, True)

        deps.append(asset.package_name)

        total_memory = 0
        total_ref_count = 0

        for package_name in deps:

            if str(package_name).startswith("/Game/"):

                package_name_hash = hash(package_name)

                if package_name_hash not in asset_memory_lookup:

                    package_system_path = ue_asset_lib.get_package_system_path(package_name)

                    if package_system_path:
                        size = os.path.getsize(package_system_path)
                        asset_memory_lookup[package_name_hash] = size
                    else:
                        continue

                total_memory += asset_memory_lookup[package_name_hash]
                total_ref_count += 1

        disk_size = int(total_memory/1000000.0)
        asset_class = ue_asset_lib.get_asset_class(asset)
        package_name = asset.package_name
        system_path = ue_asset_lib.get_package_system_path(package_name)
        user = p4.get_file_user(system_path, "both")
        date = p4.get_file_date(system_path)

        asset_hard_ref_mem.append([disk_size, total_ref_count, asset_class, package_name, user, date])

        progress_bar.make_progress()
    
    asset_hard_ref_mem_sorted = sorted(asset_hard_ref_mem)

    logger.log_ue("Scanned {} assets.\n".format(len(filtered_assets)))

    for row in asset_hard_ref_mem_sorted[::-1]:

        report.add_row(row)

    report.output_report()

    return True