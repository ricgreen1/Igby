# invalid_content_files_report_R.py for Igby UE Project Automator
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import hashlib, os, unreal, igby_lib, ue_asset_lib, module_settings

def run(settings_from_json, logger):

    #settings
    module_settings_definition = module_settings.report_module_base_settings_definition
    settings = igby_lib.validate_settings(settings_from_json, module_settings_definition, logger)

    #setup report
    report = igby_lib.report(settings, logger)
    report.set_log_message("The following is a list of all actors in the level:\n")
    report.set_column_categories(["Name", "Type", "Location", "bounds", "bounds area", "external actor path", "spatially loaded", "runtime grid"])

    filtered_assets = ue_asset_lib.get_assets(settings["PATHS_TO_INCLUDE"], settings["PATHS_TO_IGNORE"], True)
    all_worlds = []

    for asset in filtered_assets:
        if ue_asset_lib.get_asset_class(asset) == "World":
            all_worlds.append(asset)

    editor_actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    level_editor_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

    world_count = 0
    total_worlds = len(all_worlds)

    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()

    for world in all_worlds:

        info = []

        world_count+=1
        logger.log_ue(f"\nProcessing Level {world_count}/{total_worlds}: {world.package_name}")

        report_string_parts = str(world.package_name)[6:].rsplit('/',1)
        report_string = f"{report_string_parts[1]}({report_string_parts[0].replace('/','%')})"
        report.set_report_subdir(report_string)
        report.set_report_file_name_prefix(report_string_parts[1])

        external_actors_path = str(world.package_name).replace("/Game/","/Game/__ExternalActors__/")
        all_level_assets = asset_registry.get_assets_by_path(external_actors_path, True)

        use_external_actors = len(all_level_assets) > 0

        all_level_actors = list()

        if use_external_actors:

            for asset_data in all_level_assets:

                if asset_data.get_class() is None:
                    all_level_actors.append(asset_data.package_name)
                else:
                    actor_asset = asset_data.get_asset()
                    all_level_actors.append(actor_asset)

        else:

            level_editor_subsystem.load_level(world.package_name)
            all_level_actors = editor_actor_subsystem.get_all_level_actors()

        #process all actors
        total_level_actors = len(all_level_actors)
        progress_bar = igby_lib.long_process(total_level_actors, logger)

        for actor in all_level_actors:

            actor_info = []

            if type(actor) is unreal.Name:

                actor_info = ["", "None", "", "", "", actor]
         
            else:

                actor_name = actor.get_actor_label()
                actor_class = actor.__class__.__name__
                location = actor.get_actor_location()
                actor_location = f"({location.x:.2f} {location.y:.2f} {location.z:.2f})"
                bounds = actor.get_actor_bounds(False, False)[1]
                actor_bounds = f"({bounds.x:.2f} {bounds.y:.2f} {bounds.z:.2f})"
                actor_bounds_area = f"{(bounds.x * bounds.y * bounds.z):.2f}"
                actor_info = [actor_name, actor_class, actor_location, actor_bounds, actor_bounds_area]

                if use_external_actors:
                    external_actor_path = actor.get_package().get_name()
                    spatially_loaded = actor.get_editor_property("is_spatially_loaded")
                    runtime_grid = actor.get_editor_property("runtime_grid")
                    actor_info.extend([external_actor_path, spatially_loaded, runtime_grid])

            info.append(actor_info)

            progress_bar.make_progress()

        if len(info):

            info = sorted(info, key=lambda x: x[0])
            
            for row in info:
                report.add_row(row)

            report.output_report()

    return True