# invalid_content_files_report_R.py for Igby UE Project Automator
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import unreal, igby_lib, ue_asset_lib, module_settings

def run(settings_from_json, logger, p4):

    #settings
    module_settings_definition = {}
    module_settings_definition.update(module_settings.content_path_base_settings_definition.copy())
    module_settings_definition.update(module_settings.report_module_base_settings_definition.copy())
    settings = igby_lib.validate_settings(settings_from_json, module_settings_definition, logger)

    #setup report
    report = igby_lib.report(settings, logger)
    report.set_log_message("The following is a list of all levels and corresponding info:\n")
    report.set_column_categories(["name", "external actors", "actor count", "disk size Mb", "user", "date"])

    #description
    logger.log_ue("Getting level info.\n")

    #guidance
    logger.log_ue("This information can help identify levels that are no longer being used.\n", "info_clr")

    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    filtered_assets = ue_asset_lib.get_assets(settings["PATHS_TO_INCLUDE"], settings["PATHS_TO_IGNORE"], True)

    world_filter = unreal.ARFilter(class_names=["World"])
    all_worlds = asset_registry.run_assets_through_filter(filtered_assets, world_filter)

    editor_actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    level_editor_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

    total_worlds = len(all_worlds)
    progress_bar = igby_lib.long_process(total_worlds, logger)

    world_info = []

    for world in all_worlds:

        external_actors_path = str(world.package_name).replace("/Game/","/Game/__ExternalActors__/")
        all_level_actors = asset_registry.get_assets_by_path(external_actors_path, True)

        use_external_actors = len(all_level_actors) > 0

        level_system_path = ue_asset_lib.get_package_system_path(world.package_name)
        disk_space = ue_asset_lib.get_package_disk_size(world.package_name, "mb")

        if not use_external_actors:

            level_editor_subsystem.load_level(world.package_name)
            all_level_actors = editor_actor_subsystem.get_all_level_actors()
            date = p4.get_file_date(level_system_path)
            user = p4.get_file_user(level_system_path, "last")
        
        else:

            level_date = p4.get_file_date(level_system_path, "last", False)
            most_recent_date = level_date
            most_recent_actor_system_path = level_system_path

            for level_actor in all_level_actors:
                
                actor_system_path  = ue_asset_lib.get_package_system_path(level_actor.package_name)
                actor_file_date = p4.get_file_date(actor_system_path, "last", False)
                if actor_file_date > most_recent_date:
                    most_recent_date = actor_file_date
                    most_recent_actor_system_path = actor_system_path

                disk_space += ue_asset_lib.get_package_disk_size(level_actor.package_name, "mb")

            date = p4.get_file_date(most_recent_actor_system_path)
            user = p4.get_file_user(most_recent_actor_system_path, "last")
        
        disk_space = int(disk_space*1000)/1000.0

        actor_count = len(all_level_actors)
        world_info.append([world.package_name, use_external_actors, actor_count, disk_space, user, date])

        progress_bar.make_progress()

    logger.log_ue(f"Scanned {total_worlds} levels.\n")

    if len(world_info):

        world_info = sorted(world_info, key=lambda x: x[0])
        
        for row in world_info:
            report.add_row(row)

        report.output_report()

    return True