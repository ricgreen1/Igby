# module_settings.py for Igby UE Project Automator
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import igby_lib

content_path_base_settings_definition = {
"PATHS_TO_INCLUDE":{"type":"list(str)", "default":["/Game"], "info":"UE content folders where assets will be included in the analysis."},
"PATHS_TO_IGNORE":{"type":"list(str)", "default":["/Game/Developers"], "info":"UE content folders where assets will be excluded from the analysis."},
}

report_settings_defenition = igby_lib.report.report_settings_defenition
report_module_base_settings_definition = content_path_base_settings_definition.copy()
report_module_base_settings_definition.update(report_settings_defenition)