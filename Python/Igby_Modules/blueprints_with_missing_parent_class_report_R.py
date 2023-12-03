# blueprints_with_missing_parent_class_report_R.py for Igby UE Project Automator
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
    report.set_log_message("The following is a list of blueprints that are missing a parent class:\n")
    report.set_column_categories(["blueprint", "user", "date"])

    #description
    logger.log_ue("Identifying blueprints that are missing a parent class.")

    #guidance
    logger.log_ue("This is usually due to a parent class that has not been submitted or been deleted.", "info_clr")
    logger.log_ue("These blueprints should be remapped to an existing class or removed to improve project integrity.\n", "info_clr")

    #logic
    total_asset_count = 0

    filtered_assets = ue_asset_lib.get_assets(settings["PATHS_TO_INCLUDE"], settings["PATHS_TO_IGNORE"], True)
    blueprint_assets = ue_asset_lib.filter_assets_of_class(filtered_assets, "Blueprint", "keep")

    blueprints_with_missing_parent_class = list()

    progress_bar = igby_lib.long_process(len(blueprint_assets), logger)

    for blueprint in blueprint_assets:

        total_asset_count+=1

        object_path = ue_asset_lib.get_object_path(blueprint)

        bp_class_object_path = '{}_C'.format(object_path)
        bp_gen_object = unreal.load_asset(bp_class_object_path)
        blueprint_class_default = unreal.get_default_object(bp_gen_object)

        if isinstance(blueprint_class_default, type(None)):

            package_name = blueprint.package_name
            system_path = ue_asset_lib.get_package_system_path(package_name)
            user = p4.get_file_user(system_path, "both")
            date = p4.get_file_date(system_path)
            
            blueprints_with_missing_parent_class.append([package_name, user, date])

        progress_bar.make_progress()

    blueprints_with_missing_parent_class = sorted(blueprints_with_missing_parent_class)

    logger.log_ue("Scanned {} blueprints.\n".format(total_asset_count))

    for row in blueprints_with_missing_parent_class:

        report.add_row(row)

    report.output_report()

    return True