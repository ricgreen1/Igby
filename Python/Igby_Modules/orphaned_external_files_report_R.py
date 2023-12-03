# orphaned_external_files_report_R.py for Igby UE Project Automator
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import os, unreal, igby_lib, module_settings

def run(settings_from_json, logger, p4):

    #settings
    module_settings_definition = {}
    module_settings_definition.update(module_settings.content_path_base_settings_definition.copy())
    module_settings_definition.update(module_settings.report_module_base_settings_definition.copy())
    settings = igby_lib.validate_settings(settings_from_json, module_settings_definition, logger)

    #setup report
    report = igby_lib.report(settings, logger)
    report.set_log_message("The following is a list of all orphaned external actor directories:\n")
    report.set_column_categories(["orphaned external actor path", "external actor count", "disk size mb", "date", "user"])

    #description
    logger.log_ue("Identifying orphaned external actor directories.\n")

    #guidance
    logger.log_ue("The orphaned external actor directories should be cleaned up to improve project integrity.\n", "info_clr")
 
    rel_content_path = unreal.Paths.project_content_dir()
    abs_content_path = unreal.Paths.convert_relative_path_to_full(rel_content_path).replace('/','\\')
    
    external_actor_path = f"{abs_content_path}__ExternalActors__"
    checked_dirs = []
    info = []

    dir_count = 0

    for r, d, f in os.walk(external_actor_path):

        dir_count += 1
        for file in f:

            file_l = file.lower()

            if file_l.endswith(".uasset"):

                external_level_dir = r.rsplit("\\",2)[0]
                level_path = external_level_dir.replace("__ExternalActors__\\","")
                parent_level = f"{level_path}.umap"

                if external_level_dir not in checked_dirs:

                    most_recent_date = 0
                    disk_space = 0
                    external_actor_count = 0

                    if not os.path.isfile(parent_level):

                        #get last update external actor info
                        for r2, d2, f2 in os.walk(external_level_dir):

                            for external_actor_file in f2:

                                external_actor_file_path = (os.path.join(r2, external_actor_file))
                                actor_file_date = p4.get_file_date(external_actor_file_path, "last", False)

                                if actor_file_date > most_recent_date:
                                    most_recent_date = actor_file_date
                                    most_recent_actor_system_path = external_actor_file_path

                                disk_space += igby_lib.get_file_disk_size(external_actor_file_path, "mb")
                                external_actor_count+=1

                        date = p4.get_file_date(most_recent_actor_system_path)
                        user = p4.get_file_user(most_recent_actor_system_path, "last")
                        info.append([external_level_dir, external_actor_count, disk_space, date, user])
                    
                    checked_dirs.append(external_level_dir)

                break

    logger.log_ue(f"Scanned {dir_count} directories.\n")

    for row in info:
        report.add_row(row)

    report.output_report()

    return True