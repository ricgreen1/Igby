![Igby](http://i.imgur.com/zvlpKNL.png)

# Please send feeback and feature requests to [rg.igby@gmail.com](mailto:rg.igby@gmail.com)

[Twitter](https://twitter.com/igby_io) | [Discord](https://discord.gg/S9JAjBFJWw) | [igby.io](https://igby.io) | [Contact](mailto:rg.igby@gmail.com) | [Buy me coffe :)](https://ko-fi.com/ricgreen1)
# Unreal Engine Automation Platform

## To achieve success, one must make sound decisions. Sound decisions require focused and accurate information. When information is always within reach, you have no excuses.

## What is Igby?

Artists should be creating breathtaking visuals.\
Designers should iterate over gameplay to create a one of a kind experience.\
Programmers need the focus to develop groundbreaking features and systems.

How do you empower everyone on the team while giving them the freedom to focus on their craft?\
How do you identify problems before they lead to frustration and downtime?\
How do you stop wasting money and man hours on mundane yet necessary tasks?\

**You let Igby do it for you!**

Why let igby run tasks when a user can run them on demand?\
Igby works in an isolated environment and always has the latest data that is unmodified in any way.\
Some tasks take a long time to complete, and letting your team run tasks is tedious and time consuming.\
Igby reports contain histsorical information which can be handy when tracking down the origin of an issue.\

Igby utilizes The Unreal Engine and Python API in conjunction with the Perforce python library to continuously sync and run [**modules**](#included-modules) that perform specific tasks. This system can be used to generate asset/level reports which will give you detailed insights into the pieces that make up the project. Igby also monitors the project for problems and can apply automatic solutions. All of this information will be ultimately available on demand or as subscribed alerts. You will react to problems as they occur and even use insights to avoid problems that can slow down or even cripple production. Using python provides complete source code transparency, simple project integration and enables a broader audience to utilize Igby and author additional modules to address specific needs.

## Requirements

Unreal Engine 4.27 or newer.\
Perforce repository.\
Python 3.7.7 or newer.\
Unreal Game Sync (optional)

## Motivation and Future Plans

I believe that managing project integrity is an important task, and as projects become more complex there will be more issues to track and fix. As the dataset grows it becomes more difficult to track progress and be in tune with the health of the project content. Every team tends to build their own custom solution to solve these issues, but these solutions are seldom shared. I was between jobs and had some free time and plenty of ideas, and so I set off on this journey. I learned a lot and hopefully made something that others will use and appreciate. This is an opportunity to alleviate stress from the team, while making information and solutions intuitive and readily available for content creators and production alike. In the future igby will have insights that will let you debug using historical stats and help you see where the project is headed. I am proud of what I have accomplished so far, but know that there is still a lot of work to be done. My goal is to continue to work on Igby features/improvements as well as expansion of the Igby module library. So if you have any suggestions/requests or just want to say hi, please send me an email to rg.igby@gmail.com

## What Are Modules?

Modules are unique scripts that you can choose to run on your project. Module description is provided at the top of each .py file.
Currently modules come in 2 varieties:
1. Modules that only read data to gather and display information will have an "R" at the end.
2. Modules that modify the assets and submit them into Perforce will have an "S" at the end.

<img src="https://i.imgur.com/vxaFFve.gif" alt="drawing" style="width:387px;"/>

## Included Modules: 

:white_check_mark: **texture_info_report_R** - This module provides valuable information about textures in your project.

:white_check_mark: **asset_hard_reference_report_R** - This module generates a report of assets that have large dependency chains. Large dependency chains could cause slow loads and other complications. It is recommended to replace hard references with soft references that can be loaded on demand and even asynchronously.

:white_check_mark: **asset_with_prohibited_dependencies_report_R** - This module generates a report of assets that have dependencies in prohibited folders. For example you can identify assets outside of the developer folder that contain dependencies inside the developer folder.

:white_check_mark: **dual_asset_package_report_R** - This module generates a report of packages that contain more than one asset. Sometimes unreal generates packages with multiple assets. This does not occur often but could result in errors when certain operations are applied. Packages with multiple assets also result in multiple assets being locked up when one is being worked on. I recommend identifying such assets and splitting them up into individual packages when possible.

:white_check_mark: **unused_assets_report_R** - This module identifies unused assets and presents them as a list. The resulting report can be used as guidance for which assets should be cleaned out from the project.

:white_check_mark: **asset_type_count_report_R** - This module identifies project assets and tabulates a total count for each asset type.

:white_check_mark: **blueprints_with_missing_parent_class_report_R** - This module identifies blueprints that are missing a parent class. These blueprints are likely in a broken state and can either be re-parented to an existing class or deleted.

:white_check_mark: **invalid_content_files_report_R** - This module identifies .uasset and .umap files that are no longer recognized by Unreal Engine and therefore can be removed from the project.

:white_check_mark: **asset_source_availability_report_R** - This module identifies imported assets with source files that are not in the Perforce depot.

:white_check_mark: **level_actor_report_R** - This report contains level actor information. Support both regular and external actor levels.

:white_check_mark: **level_report_R** - This report per level information that will enable you to make informative decisions.

:white_check_mark: **redirector_cleaner_S** - This module will automatically fix up redirectors.

:white_check_mark: **orphaned_external_files_report_R** - This module will identify external actor files that are orphaned because their corresponding world asset no longer exists.

(There are lots of useful modules planned so stay tuned!)

## Report Sample

<img src="https://i.imgur.com/DVwXeze.jpeg" alt="drawing"/>

## The Loop

<img src="https://i.imgur.com/431BJYH.jpg" alt="drawing" width="422"/>

## Setup

Igby is self contained and only requires 4 setup steps:
1. Copy the whole igby folder to one of your local drives. Make sure it has ample storage space.
2. Create a dedicated Perforce user and clientspec.
3. Create a [igby_python] environment variable that points to the python executable that you want Igby to use.\
    Which python should I use?\
    A. You can use the python executable that ships with your version of UE.\
          [UE install path]\Engine\Binaries\ThirdParty\Python3\Win64\python.exe\
    B. You can download and install python 3.7.# or 3.9.# from [python.org](https://www.python.org/downloads/)
5. Create a custom version of the included [sample_igby_settings.json] file to reflect your settings.

## Settings - json:

Here is what an example settings file looks like

```json
{
    "LOG_PATH":"D:\\Sample_Project\\Igby\\Logs\\Igby_Sample_Project_Log.txt",
    "MIN_WAIT_SEC":600,
    "MAX_RUNS":0,
    "P4_PORT":"0.0.0.0:1666",
    "P4_USER":"user_name", 
    "P4_CLIENT":"user_DESKTOP-F4B2F5M_6315",
    "P4_CL_DESCRIPTION_PREFIX":"#Igby Automation",
    "P4_CHARSET":"utf8",
    "PRE_RUN_PYTHON_COMMAND":"sample_pre_run_command.run()",
    "P4_DIRS_TO_SYNC":[],
    "UGS_EXE_PATH":"C:\\Users\\username\\AppData\\Local\\UnrealGameSync\\Latest\\ugs.exe",
    "UE_CMD_EXE_PATH":"D:\\Unreal\\Engine\\Binaries\\Win64\\UnrealEditor-Cmd.exe",
    "UE_PROJECT_PATH":"D:\\Sample_Project\\project.uproject",
    "HALT_ON_ERROR":true,
    "FORCE_RUN":true,
    "PROJECT_CONTENT_INTEGRITY_TEST":true,
    "PY_LIBS":{"slackclient":{"module":"slack"}},
    "MODULE_SETTING_PRESETS":{
        "REPORT_SETTINGS":{
            "PATHS_TO_INCLUDE":["/Game/"],
            "PATHS_TO_IGNORE":["/Game/Developers/"],
            "REPORT_SAVE_DIR":"D:\\Sample_Project\\Igby\\Reports\\",
            "REPORT_ONLY_SAVE_UNIQUE":true,
            "REPORT_MODULE_NAME":""
        }
    },
    "MODULES_TO_RUN":[
        {"invalid_content_files_report_R":{
            "INCLUDE_MODULE_SETTING_PRESETS":["REPORT_SETTINGS"]
            }
        },
        {"blueprints_with_missing_parent_class_report_R":{
            "INCLUDE_MODULE_SETTING_PRESETS":["REPORT_SETTINGS"]
            }
        },
        {"asset_hard_reference_report_R":{
            "INCLUDE_MODULE_SETTING_PRESETS":["REPORT_SETTINGS"],
            "REPORT_LINE_LIMIT":100
            }
        },
        {"asset_type_count_report_R":{
            "INCLUDE_MODULE_SETTING_PRESETS":["REPORT_SETTINGS"]
            }
        },
        {"dual_asset_package_report_R":{
            "INCLUDE_MODULE_SETTING_PRESETS":["REPORT_SETTINGS"]
            }
        },
        {"unused_assets_report_R":{
            "INCLUDE_MODULE_SETTING_PRESETS":["REPORT_SETTINGS"]
            }
        }
    ]
}
```

Most settings are self explanatory with a few exceptions listed here.\
"PRE_RUN_PYTHON_COMMAND" (This runs a python command before every Igby run. This might be a good place to make UE updates.)\
"MIN_WAIT_SEC" (This is the minimum time in seconds Igby should wait between each run. This timer starts at the beginning of each run.)\
"MAX_RUNS" (This is how many times you want Igby to run the modules. 0 = indefinitely)\
"HALT_ON_ERROR" If this setting is set to true then Igby will halt if an error is detected.\
"FORCE_RUN" Igby is designed to run the modules only if there is new data from perforce or if a pre-run command makes updates. Setting this to true will force run the modules every time.\
"P4_PASSWORD" (If left blank Igby will prompt you for the Perforce password during the initial run.)\
"P4_CL_DESCRIPTION_PREFIX" (This is the prefix in the changelist description that you want in every changelist that Igby generates.)

Each module that you want to run should be included in the settings file with its corresponding settings as seen in the included sample sample_igby_settings.json file. The settings for each module are defined in the beginning of the run() function of the module's .py file.

## How To Run

(Windows)\
Drag your settings json file that contains the settings and drop it on igby.bat

(Cmd Shell)\
Provide the settings json file as the argument for igby.bat Ex. igby.bat my_project_settings.json

Including -d after the .json file will run igby with full verbosity for debugging purposes.

## Testing Info

Igby V1.2.0 tested with the following setup:\
Windows 11 Pro Version 10.0.22621 Build 22621\
Unreal Editor 5.1.0\
Python 3.9.7\
Perforce P4D/LINUX26X86_64/2021.2/2273812 (2022/04/14)

## Updates

9/27/22\
igby v 0.1.1 - Now works with Unreal 4.27 and Python 3.7.7\
redirector_cleaner_S - Now works with Unreal 4.27 and Python 3.7.7

9/29/22\
Added asset_hard_reference_report_R module which reports assets that have long “hard reference” dependency chains. This module will help identify assets that should be evaluated for long load/cook times.\
Added ue_asset_lib.py which has functionality that is re-used in the modules.

10/4/22\
Added UE4.27 specific bug fixes to ue_asset_lib
Added new module: asset_with_prohibited_dependenices_report_R

10/6/22\
Added unused_asset_report_R module which identifies assets that are not being used.

10/7/22\
Added blueprints_with_missing_parent_class_R module which identifies blueprints that have a missing parent class.

10/16/22\
Added asset_type_count_report_R which generates a list with total count for each represented asset class.\
Added a number that increments during ue startup. It will help you determine startup progress.\
"MODULE_DEFAULT_SETTINGS" allows you do define default settings for all modules in the settings file.\
Each module now expects a specific set of settings with defaults. Error if setting is missing. Warning if setting is deprecated.\
Added defaults for module settings defenition.\
Added progress bar with % for modules that may take a long time to run.\
Added new class for generating reports and writing them to log and .csv file.\
Added ability to truncate report log output for reports that contain a lot of info.\
Added user info to reports that identifies last user to check in file. This feature slowed down some of the scripts. Have plan to optimize in a future release.\
Optimized report modules to make up for user info related slowdown.\
Cleaned up report modules to have similar structure.\
Added faster function to get system path of package.\
Note: redirector_cleaner_S does not currently generate a report.\
Note: on occasion UE4.27 throws asset_registry errors during first run. Will work on solving this issue.

10/25/22\
Updated to support UE5.1\
Implemented p4 password security measures as requested by users.\
Fixed logging bug.

12/12/22\
v1.0.0 is here just in time for the holidays! And boy is it full of amazing features and loads of bug fixes!\
"MODULE_SETTING_PRESETS" section in the .json settings file can contain multiple presets that can be used as settings for multiple modules.\
Added setting presets for all major functions and classes.\
Setting presets can now be inherited from other setting presets.\
Setting validation makes sure settings are correct. Defaults are used if the setting is missing and defaults are available. Igby halts if crucial settings are missing.\
Added project content integrity test that makes sure tha the conent directory is synce properly.\
Reports are now deterministic between runs.\
Added option to not save duplicate reports. When enabled, igby only save the report if it's contents are different from previous report.\
Added "P4_CHARSET" option for perforce settings. (default set to utf8)\
Igby window title bar now has additional useful information.\
Added CL number to report file name.\
Lots and lots of bug fixes!\

03/30/23\
Been a while but I've been busy and v1.0.1 is here.\
Added support for Unreal Game Sync (UGS)\
Added support for adding additional python libraries via prerequisites_lib.py\
Added ue_general_lib.py This is where I will implement general ue functionality.\
Updated module_settings.py\
Added new Igby options to support new features.\
UGS_EXE_PATH = path to ugs exe.\
PY_LIBS = additional py libraries that will be supported in the future. Will work on slack integration first.\

04/11/23\
ugs_lib.py = Added tries for builds that are missing prebuilt binaries.\
ue_asset_lib.py = added some quality of life functions.\
prerequisistes_lib.py = now checks for and installs prerequisite libraries.\
perforce_helper.py = added get_root function.\
igby.py = now reports updated runs and their average run time. Updated runs are runs that executed modules.\
igby_lib.py = fixed report saving bug.\
new module = asset_source_availability_report\

04/17/23\
Updated perforce_helper.py so that it now caches the perforce data, resulting in 6x performance boost and fewer interactions with the perforce server.

04/19/23\
Cleaned up report logic for modules.\
Reports now contain "checkin" date column.\
Fixed bug that was causing reports to start on 2nd line.

04/26/23\
Added flags to enable texture and shader compilation in unreal. This will result in very slow initial editor startup that is caused by initial shader compilation. Consecutive startups should be normal.\
Added Texture_info_report_R that provides valuable texture information.

05/12/23\
Improved accuracy of identical report identification\
Added logic to handle critical UGS errors

05/16/23\
Added REPORT_LINE_LIMIT that allows to limit report items\
Removed outputting to log and log output limit. This option is no longer needed ass all reports are now written to csv files.

05/22/23\
Improved error handling and reporting for Igby and UGS lib.

05/31/23\
Sorted p4 server connection and login issues.\
Now ignoring errors that come may occur when unreal is shutting down after igby completed execution.

06/10/23\
New Report: level_actor_report_R.py This report contains level actor information. Support both regular and external actor levels.\
igby_lib = Report class updates. Now supports report file name prefix.\
perforce_helper = Updated get_file_log function to work without file_log_cache\
invalid_actor_report_R = Now identifies assets that are of class None.

08/20/23\
Apologies for not having any updates lately. I have discovered a new obsession which is pickleball. XD\
perforce_helper.py: Login defaults to perforce ticketing system. Password input will only be required when the ticket has expired.\
ugs_lib.py: Handles more issues that may arise.\
igby.py now: Identifies perforce connection issues and attempts to reconnect at the beginning of every run.\

10/02/23\
Fixed perforce connection bugs.\
Added UGS recovery from incomplete syncs.

10/08/23\
redirector_cleaner_S has been refactored and made more robust. I recommend setting up a seperate perforce workspace for modules that make changes to content. I am running one for reports that simply syncs latest and runs reports, and another workspace for modules that make content changes.\
ugs_lib.py updated to have better sync error reporting.\
igby.py now supports "SKIP_SYNC" option that will skip syncing. This is primarely used for debugging purposes. The integrity test is now more robust. There are also improvements to error verbosity.\
igby_lib.py now formatting logger input as string to make logger more robust.\
perforce_helper now has a new function for marking assets for deletion.

10/24/23\
redirector_cleaner_S now supports soft references\
igby.py now has better error reporting\
perforce_helper.py get_owner function now reports the user who has a file checked out.\

11/18/23\
igby = Igby is now v1.2 and has many improvements and bug fixes. The integrity test has been moved to a function in igby_lib. In addition to the "startup log", igby now keeps a "post startup log" for debugging purposes. Now building changelist cache. Added "handle_error" function. Improved error handling.\
igby_lib = Added "integrity_test" function.\
ugs_lib = improved error logging.\
ue_asset_lib = added "get_package_disk_size" function.\
perforce_helper_lib = refactored build_filelog_cache. added build_changelist_cache. fixed bug in def get_file_owner function. Added "best" and "both" modes to get_file_user function. Added "get_file_date" function. Updated "convert_to_depot_path" function.\
module_settings = refactored setting presets.\
All modules have a refactored "settings" setup that fixed bugs that occured when modules ran in a specific order. Also user information now represents both "last" and "best" user.\
static_mesh_report_R = New Module! Reports useful information for all static meshes.\
level_actor_report_R = Slight logic and logging improvements.\
redirector_cleaner_S = Any redirector that shares it's package with another asset will not be handled. Fixed minor bug that prevented submission of changelist in some cases.\
dual_assest_package_report_R = Improved reported information.\
asset_source_availablity_report_R = Added "ASSET_SOURCE_DIRS_FOR_P4_CACHE" setting which will add asset source files to the p4 cache.\

11/20/23\
level_actor_report_R = fixed category naming.\
level_report_R = New report module that provides per level statistics.\
perforce_helper = added format option to get_file_date function.\
igby_lib = fixed bug that would add an undersore to the names of all reports.\

12/03/23\
igby_lib.py = improved logging. improved integrity test. added unique sstartup logging function. added new function get_file_disk_size()\
igby.py = if igby submits a changelist, igby will now wait for a build that is same or newer as the submitted changelist. Improved logging. Fixed bugs.\
ugs_lib.py = added support for checking if latest build is same or newer than submitted changelist.\
orphaned_external_files_report_R.py = New module that will list all external actors that are orphaned because they do not have a corresponding world asset.\
redirector_cleaner_S.py = Updated to fix redirectors that have multiple assets but no dependencies. It will also return the submitted changelist number in order for igby to know which cl to wait for before executing next run.\
asset_hard_reference_report_R.py = Update to skip world assets, as we are primarily interested in non world assets.
