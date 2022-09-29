# asset_hard_reference_report_R.py for Igby UE Project Automator
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import os, unreal, igby_lib, ue_asset_lib

def run(settings):
    
    #get setting
    paths_to_include = settings['PATHS_TO_INCLUDE']
    paths_to_ignore = settings['PATHS_TO_IGNORE']
    show_top_count = settings['SHOW_TOP_COUNT']

    #setup logger
    logger = igby_lib.logger()
    logger.prefix = "    "

    logger.log_ue("Identifying packages that have a large hard reference chain.\n")
    logger.log_ue("To reduce the hard reference chain size, remove hard references or replace them with soft references.\n")

    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()

    asset_memory_lookup = dict()
    asset_hard_ref_mem = list()
    total_asset_count = 0

    filtered_assets = ue_asset_lib.get_assets(paths_to_include, paths_to_ignore, True)

    for asset in filtered_assets:

        total_asset_count+=1

        deps = ue_asset_lib.get_connections(asset, "dependencies", False, True, True)
        deps.append(asset.package_name)

        total_memory = 0
        total_ref_count = 0

        for package_name in deps:

            if str(package_name).startswith("/Game/"):

                if package_name in asset_memory_lookup:

                    total_memory += asset_memory_lookup[package_name]
                    total_ref_count += 1

                else:

                    assets_from_package = asset_registry.get_assets_by_package_name(package_name)
                    
                    if len(assets_from_package) > 0:

                        asset_path = unreal.SystemLibrary.get_system_path(assets_from_package[0].get_asset())

                        if os.path.isfile(asset_path):

                            asset_memory = os.path.getsize(asset_path)
                            asset_memory_lookup[package_name] = asset_memory
                            total_memory += asset_memory_lookup[package_name]
                            total_ref_count += 1

        asset_hard_ref_mem.append((total_memory, total_ref_count, asset.asset_class, asset.package_name, ))
    
    asset_hard_ref_mem_sorted = sorted(asset_hard_ref_mem)

    logger.log_ue("Scanned {} assets.\n".format(total_asset_count))

    if show_top_count == 0:
        logger.log_ue("The following is a list of all assets in descending order of hard reference chain size:\n")
    else:
        logger.log_ue("The following is a list of top {} assets with largest hard reference chain:\n".format(show_top_count))

    counter = 0

    for info in asset_hard_ref_mem_sorted[::-1]:

        logger.log_ue("{:.3f} {} {} {}".format((info[0]/1000000.0), str(info[1]), str(info[2]), str(info[3])))

        counter+=1

        if show_top_count > 0 and counter == show_top_count:
            break

    return True