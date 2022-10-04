# ue_asset_lib.py asset helper functions for Igby UE Project Automator
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import unreal

def get_assets(paths_to_include, paths_to_ignore, ignore_external_actors = True):

    #ue4 causes some path that end with / not to get recognzied.
    for i in range(len(paths_to_include)):
        if paths_to_include[i].endswith('/'):
            paths_to_include[i] = paths_to_include[i][0:-1]

    for i in range(len(paths_to_ignore)):
        if paths_to_ignore[i].endswith('/'):
            paths_to_ignore[i] = paths_to_ignore[i][0:-1]


    if ignore_external_actors:
        paths_to_ignore.append("/Game/__ExternalActors__")

    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()

    include_assets_D = dict()

    for path_to_include in paths_to_include:

        include_assets =  asset_registry.get_assets_by_path(path_to_include, True)

        #for UE4.27 remove blueprint class assets. This happens in headless unreal only.
        include_assets = remove_assets_of_class(include_assets, "BlueprintGeneratedClass")

        for asset in include_assets:

            if asset.object_path not in include_assets_D:
                include_assets_D[asset.object_path] = asset

    ignore_object_paths = set()

    for path_to_ignore in paths_to_ignore:

        ignore_assets =  asset_registry.get_assets_by_path(path_to_ignore, True)

        for asset in ignore_assets:

            ignore_object_paths.add(asset.object_path)

    include_object_paths = set(include_assets_D.keys()) - ignore_object_paths

    filtered_assets = list(include_assets_D[k] for k in include_object_paths)

    return filtered_assets


def remove_assets_of_class(assets, class_name):

    filtered_assets = list()

    for asset in assets:

        if asset.asset_class != class_name:

            filtered_assets.append(asset)

    return filtered_assets



def assets_to_package_names(assets):

    package_names = list()

    for asset in assets:

        package_names.append(asset.package_name)

    return package_names


def get_connections(object, type = "referencers", soft_refs = False, hard_refs = True, recursive = True):

    if type != "dependencies" and type != "referencers":

        raise Exception("type parameter should be either \"referencers\" or \"dependencies\"")

    referencers = False
    if type == "referencers":
        referencers = True

    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    dep_options = unreal.AssetRegistryDependencyOptions(include_soft_package_references = soft_refs, include_hard_package_references = hard_refs, include_searchable_names=False, include_soft_management_references=False, include_hard_management_references=False)

    object_package_name = object.package_name
    package_names = set([object_package_name])
    all_connections = package_names

    all_connections_len_start = -1
    all_connections_len_end = 0

    while all_connections_len_start < all_connections_len_end:

        all_connections_len_start = len(all_connections)
        package_names_new = set()

        for package_name in package_names:

            if referencers:
                connections = set(asset_registry.get_referencers(package_name, dep_options))
            else:
                connections = set(asset_registry.get_dependencies(package_name, dep_options))

            package_names_new.update(connections)
        
        package_names = package_names_new - all_connections

        all_connections.update(package_names)

        if recursive:

            all_connections_len_end = len(all_connections)

        else:

            break

    all_connections = all_connections - set([object_package_name])

    return list(all_connections)


def class_only_test(package_names, class_name):

    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    class_only = True

    for package_name in package_names:

        assets = asset_registry.get_assets_by_package_name(package_name)

        for asset in assets:

            if asset.asset_class != class_name:
                class_only = False
                break
        
        if not class_only:
            break

    return class_only