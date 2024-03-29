# ue_asset_lib.py asset helper functions for Igby UE Project Automator
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import unreal, os, igby_lib

try:
    getattr(unreal, "EditorAssetLibrary")
except:
    raise(Exception("Error! Please enable the \"Editor Scripting Utilities\" plugin."))

def get_assets(paths_to_include, paths_to_ignore, ignore_external_actors = True, ignore_external_objects = True):

    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()

    #ue4 causes some path that end with / not to get recognzied.
    for i in range(len(paths_to_include)):
        if paths_to_include[i].endswith('/'):
            paths_to_include[i] = paths_to_include[i][0:-1]

    for i in range(len(paths_to_ignore)):
        if paths_to_ignore[i].endswith('/'):
            paths_to_ignore[i] = paths_to_ignore[i][0:-1]


    if ignore_external_actors:
        paths_to_ignore.append("/Game/__ExternalActors__")

    if ignore_external_objects:
        paths_to_ignore.append("/Game/__ExternalObjects__")

    include_assets_D = dict()

    for path_to_include in paths_to_include:

        include_assets =  asset_registry.get_assets_by_path(path_to_include, True)

        #for UE4.27 remove blueprint class assets. This happens in headless unreal only.
        include_assets = filter_assets_of_class(include_assets, "BlueprintGeneratedClass", "remove")

        for asset in include_assets:

            object_path = get_object_path(asset)

            if object_path not in include_assets_D:
                include_assets_D[object_path] = asset

    ignore_object_paths = set()

    for path_to_ignore in paths_to_ignore:

        ignore_assets =  asset_registry.get_assets_by_path(path_to_ignore, True)

        for asset in ignore_assets:

            ignore_object_paths.add(get_object_path(asset))

    include_object_paths = set(include_assets_D.keys()) - ignore_object_paths
    include_object_paths = sorted(include_object_paths)

    filtered_assets = list(include_assets_D[k] for k in include_object_paths)

    return filtered_assets


def get_object_path(AssetData_obj):

    object_path = f"{AssetData_obj.package_name}.{AssetData_obj.asset_name}"

    return object_path


def get_asset_class(AssetData_obj):

    asset_class = None

    if hasattr(AssetData_obj, 'asset_class_path'):
        asset_class = AssetData_obj.asset_class_path.asset_name
    else:
        asset_class = AssetData_obj.asset_class

    return asset_class


def filter_assets_of_class(assets, class_name, mode = "keep"):

    if mode != "keep" and mode != "remove":

        raise Exception("mode parameter should be either \"keep\" or \"remove\"")

    filtered_assets = list()

    if mode is "keep":

        for asset in assets:

            if get_asset_class(asset) == class_name:

                filtered_assets.append(asset)

    else:

        for asset in assets:
            
            if get_asset_class(asset) != class_name:

                filtered_assets.append(asset)

    return filtered_assets


def assets_to_package_names(assets):

    package_names = list()

    for asset in assets:

        package_names.append(asset.package_name)

    return package_names


def get_connections(object, type = "referencers", soft_refs = False, hard_refs = True, recursive = True):

    object_package_name = object.package_name
    all_connections = get_package_connections(object_package_name, type, soft_refs, hard_refs, recursive)
    return all_connections

def get_package_connections(package_name, type = "referencers", soft_refs = False, hard_refs = True, recursive = True):

    if type != "dependencies" and type != "referencers":

        raise Exception("type parameter should be either \"referencers\" or \"dependencies\"")

    referencers = False
    if type == "referencers":
        referencers = True

    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    dep_options = unreal.AssetRegistryDependencyOptions(include_soft_package_references = soft_refs, include_hard_package_references = hard_refs, include_searchable_names=False, include_soft_management_references=False, include_hard_management_references=False)

    object_package_name = package_name
    package_names = set([object_package_name])
    all_connections = package_names

    all_connections_len_start = -1
    all_connections_len_end = 0

    while all_connections_len_start < all_connections_len_end:

        all_connections_len_start = len(all_connections)
        package_names_new = set()

        for package_name in package_names:

            if referencers:
                connections = set(asset_registry.get_referencers(package_name, dep_options) or [])
            else:
                connections = set(asset_registry.get_dependencies(package_name, dep_options) or [])

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

    for package_name in package_names:

        assets = asset_registry.get_assets_by_package_name(package_name)

        if not assets_class_only_test(assets, class_name):
                return False
        
    return True


def assets_class_only_test(assets, class_name):
    
    for asset in assets:
        if get_asset_class(asset) != class_name:
            return False
        
    return True


def get_package_system_path(package_name):

    rel_content_path = unreal.Paths.project_content_dir()
    abs_content_path = unreal.Paths.convert_relative_path_to_full(rel_content_path)
    package_system_path = str(package_name).replace("/Game/",abs_content_path)

    package_system_path_with_extension = f"{package_system_path}.uasset"

    if not os.path.isfile(package_system_path_with_extension):

        package_system_path_with_extension = f"{package_system_path}.umap"

        if not os.path.isfile(package_system_path_with_extension):

            package_system_path_with_extension = None
    
    return package_system_path_with_extension


def get_package_disk_size(package_name, unit = "b"):

    package_system_path = get_package_system_path(package_name)

    disk_size = igby_lib.get_file_disk_size(package_system_path, unit)

    return disk_size


def get_all_tags(package_name):

    editor_asset_subsystem = unreal.EditorAssetSubsystem()
    all_tags = editor_asset_subsystem.get_tag_values(package_name)

    return all_tags