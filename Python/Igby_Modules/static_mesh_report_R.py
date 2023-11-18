# material_slot_count_R.py for Igby UE Project Automator
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import igby_lib, ue_asset_lib, module_settings, unreal

def run(settings_from_json, logger, p4):

    #settings
    module_settings_definition = {}
    module_settings_definition.update(module_settings.content_path_base_settings_definition.copy())
    module_settings_definition.update(module_settings.report_module_base_settings_definition.copy())
    settings = igby_lib.validate_settings(settings_from_json, module_settings_definition, logger)

    #setup report
    report = igby_lib.report(settings, logger)
    report.set_log_message("The following is a list of static meshes and their contents:\n")
    report.set_column_categories(["name", "nanite enabled", "triangle count", "material slot count", "uv channels", "disk size Mb", "user", "date"])

    #description
    logger.log("Getting static mesh content information.\n")

    #guidance
    logger.log("This information can help identify meshes that have redundant or bloated content.\n", "info_clr")

    #logic
    filtered_assets = ue_asset_lib.get_assets(settings['PATHS_TO_INCLUDE'], settings['PATHS_TO_IGNORE'])

    material_slot_info = {}

    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    static_mesh_class_path = unreal.TopLevelAssetPath(package_name = "/Script/Engine", asset_name="StaticMesh")
    static_mesh_filter = unreal.ARFilter(class_paths=[static_mesh_class_path])
    static_mesh_class_assets = asset_registry.run_assets_through_filter(filtered_assets, static_mesh_filter)

    progress_bar = igby_lib.long_process(len(static_mesh_class_assets), logger)

    for asset in static_mesh_class_assets:

        package_name = asset.package_name
 
        nanite_enabled = asset.get_tag_value('NaniteEnabled') == "True"

        if nanite_enabled:
            triangle_count = asset.get_tag_value('NaniteTriangles')
        else:
            triangle_count = asset.get_tag_value('Triangles')

        material_count = asset.get_tag_value('Materials')
        uv_channels = asset.get_tag_value('UVChannels')
        disk_size = ue_asset_lib.get_package_disk_size(package_name, "mb")
        disk_size = int(disk_size*1000.0)/1000.0
        system_path = ue_asset_lib.get_package_system_path(package_name)
        user = p4.get_file_user(system_path, "both")
        date = p4.get_file_date(system_path)

        material_slot_info[package_name] = [package_name, nanite_enabled, triangle_count, material_count, uv_channels, disk_size, user, date]

        progress_bar.make_progress()

    material_slot_info = dict(reversed(sorted(material_slot_info.items(), key=lambda item: item[1][0])))

    logger.log_ue("Scanned {} assets.\n".format(len(filtered_assets)))

    for package_name in material_slot_info:

        report.add_row(material_slot_info[package_name])

    report.output_report()

    return True