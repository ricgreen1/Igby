# texture_info_report_R.py for Igby UE Project Automator
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import igby_lib, ue_asset_lib, module_settings, unreal, time

def run(settings_from_json, logger, p4):

    #settings
    module_settings_definition = module_settings.report_module_base_settings_definition
    settings = igby_lib.validate_settings(settings_from_json, module_settings_definition, logger)

    #setup report
    report = igby_lib.report(settings, logger)
    report.set_log_message("The following is a list of textures and their info:\n")
    report.set_column_categories(["name", "size kb", "assest pixel count", "asset dimensions", "source dimensions", "compression", "type", "user", "date"])

    #description
    logger.log_ue("Getting texture info.\n")

    #guidance
    logger.log_ue("This information can help identify textures that are not setup correctly.\n", "info_clr")

    #logic
    filtered_assets = ue_asset_lib.get_assets(settings['PATHS_TO_INCLUDE'], settings['PATHS_TO_IGNORE'], True)

    progress_bar = igby_lib.long_process(len(filtered_assets), logger)

    texture_classes = ["Texture2D", "TextureCube", "VolumeTexture", "TextureRenderTarget2D"]

    texture_info = {}

    #mip_options = unreal.TextureMipLoadOptions.ALL_MIPS
    #mip_setting = unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS

    for asset in filtered_assets:

        asset_class = ue_asset_lib.get_asset_class(asset)

        if asset_class in texture_classes:
 
            package_name = asset.package_name
       
            texture_object = asset.get_asset()
            size = texture_object.blueprint_get_memory_size()/1024
            source_dimensions = asset.get_tag_value('Dimensions')
            max_texture_size = texture_object.max_texture_size

            if source_dimensions != None:
                s_dimensions = source_dimensions.split('x')
                e_dim_x = int(s_dimensions[0])
                e_dim_y = int(s_dimensions[1])

                if max_texture_size != 0:
                    e_dim_x = min(e_dim_x,max_texture_size)
                    e_dim_y = min(e_dim_y,max_texture_size)

                asset_dimensions = f"{e_dim_x}x{e_dim_y}"
                asset_total_pixels = e_dim_x * e_dim_y
            else:
                asset_total_pixels = 0
                asset_dimensions = "0x0"
                source_dimensions = "0x0"

            compression = asset.get_tag_value('CompressionSettings')
            system_path = ue_asset_lib.get_package_system_path(package_name)
            user = p4.get_file_user(system_path)
            date = p4.get_file_date(system_path)

            texture_info[package_name] = [package_name, size, asset_total_pixels, asset_dimensions, source_dimensions, compression, asset_class, user, date]

        progress_bar.make_progress()

    texture_info = dict(reversed(sorted(texture_info.items(), key=lambda item: item[1][0])))

    logger.log_ue("Scanned {} assets.\n".format(len(filtered_assets)))

    for package_name in texture_info:

        report.add_row(texture_info[package_name])

    report.output_report()

    return True