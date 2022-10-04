# asset_with_prohibited_dependenices_report_R.py for Igby UE Project Automator
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import os, unreal, igby_lib, ue_asset_lib

def run(settings):
    
    #get setting
    paths_to_include = settings['PATHS_TO_INCLUDE']
    paths_to_ignore = settings['PATHS_TO_IGNORE']
    prohibited_dependency_paths = settings['PROHIBITED_DPENDENCY_PATH']

    #setup logger
    logger = igby_lib.logger()
    logger.prefix = "    "

    logger.log_ue("Identifying packages that have dependencies from a prohibited path.")
    logger.log_ue("Prohibited dependencies should be fixed to ensure project indegrity.\n")

    total_asset_count = 0

    filtered_assets = ue_asset_lib.get_assets(paths_to_include, paths_to_ignore, True)
    prohibited_assets = ue_asset_lib.get_assets(prohibited_dependency_paths, [], True)

    prohibited_package_names = set()

    for prohibited_asset in prohibited_assets:

        prohibited_package_names.add(prohibited_asset.package_name)

    assets_with_prohibited_dependencies = {}

    for asset in filtered_assets:

        total_asset_count+=1

        deps = ue_asset_lib.get_connections(asset, "dependencies", False, True, True)

        for dep in deps:
            
            if dep in prohibited_package_names:

                if asset.object_path in assets_with_prohibited_dependencies:
                    assets_with_prohibited_dependencies[asset.object_path].append(dep)
                else:
                    assets_with_prohibited_dependencies[asset.object_path] = [dep]

    logger.log_ue("Scanned {} assets.\n".format(total_asset_count))

    logger.log_ue("The following is a list of assets and their dependencies from prohibited paths:\n")

    for asset in assets_with_prohibited_dependencies:

        logger.log_ue("")
        logger.log_ue("{}".format(asset))

        for prohibited_dep in assets_with_prohibited_dependencies[asset]:

            logger.log_ue("    {}".format(prohibited_dep))

    return True