# asset_type_count_report_R.py for Igby UE Project Automator
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import igby_lib, ue_asset_lib, module_settings

def run(settings_from_json, logger):

    #settings
    module_settings_definition = {}
    module_settings_definition.update(module_settings.content_path_base_settings_definition.copy())
    module_settings_definition.update(module_settings.report_module_base_settings_definition.copy())
    settings = igby_lib.validate_settings(settings_from_json, module_settings_definition, logger)

    #setup report
    report = igby_lib.report(settings, logger)
    report.set_log_message("The following is a list of asset types and their count:\n")
    report.set_column_categories(["count", "asset type"])

    #description
    logger.log_ue("Getting asset types and their count.\n")

    #guidance
    logger.log_ue("This information can identify unknown asset usage as well as determine development focus.\n", "info_clr")

    #logic
    filtered_assets = ue_asset_lib.get_assets(settings['PATHS_TO_INCLUDE'], settings['PATHS_TO_IGNORE'], True)

    asset_type_count = {}

    for asset in filtered_assets:

        asset_class = ue_asset_lib.get_asset_class(asset)

        if asset_class == "Blueprint":

            parent_class = asset.get_tag_value("ParentClass").split(".")[-1][0:-1]
            asset_class = "{} ({})".format(parent_class, asset_class)

        if asset_class in asset_type_count:
            
            asset_type_count[asset_class] += 1

        else:

            asset_type_count[asset_class] = 1

    asset_type_count = dict(reversed(sorted(asset_type_count.items(), key=lambda item: item[1])))

    logger.log_ue("Scanned {} assets.\n".format(len(filtered_assets)))

    for asset_type in asset_type_count:

        report.add_row([asset_type_count[asset_type], asset_type])

    report.output_report()

    return True