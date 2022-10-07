![Igby](https://i.imgur.com/Ps3nojF.png)
# Unreal Engine Automation Platform - Python

[**What is Igby?**](#what-is-igby)\
[**Motivation and Future Plans**](#motivation-and-future-plans)\
[**The Loop**](#the-loop)\
[**Setup**](#setup)\
[**Settings**](#settings---json)\
[**How To Run**](#how-to-run)\
[**Testing Info**](#testing-info)\
[**What Are Modules?**](#what-are-modules)\
[**Included Modules**](#included-modules)\
[**Key Updates**](#key-updates)

![Igby](https://i.imgur.com/vxaFFve.gif)

## What is Igby?

Igby utilizes The Unreal Engine CLI and Python API in conjunction with the Perforce python library to continuously sync and run modules on UE project content. This system can be used to Generate Reports, Monitor For Problems as well as Fix Problems. Using python provides complete source code transparency, simple project integration and enables a broader audience to utilize Igby as well as author additional modules for their specific needs.

## Motivation and Future Plans

I believe that managing project integrity is an important task, and as the games become more complicated there will be more issues to track and fix. As the dataset grows it becomes more difficult to track progress and be in tune with the health of the project content. Every team tends to build their own custom solution to solve these issues, but these solutions are seldom shared. I was between jobs and had some free time and plenty of ideas, and so I set off on this journey. I learned a lot and hopefully made something that others will use and appreciate. This is an opportunity to alleviate stress from the team, while making information and solutions intuitive and readily available for content creators and production alike. In the future igby will have insights that will let you debug using historical stats and help you see where the project is headed. I am proud of what I have accomplished so far, but know that there is still a lot of work to be done. My goal is to continue to work on Igby features/improvements as well as expansion of the Igby module library. So if you have any suggestions/requests or just want to say hi, please send me an email to rg.igby@gmail.com

## The Loop

<img src="https://i.imgur.com/431BJYH.jpg" alt="drawing" width="422"/>

## Setup

Igby is self contained and only requires 4 setup steps:
1. Copy the whole igby folder to one of your local drives. Make sure it has ample storage space.
2. Create a dedicated Perforce user and clientspec.
3. Create a [igby_python] environment variable that points to the python executable that you want Igby to use.
4. Create a custom version of the included [sample_igby_settings.json] file to reflect your settings.

## Settings - json:

Here is what an example settings file looks like

```json
{
    "LOG_PATH":"D:\\Sample_Project\\Igby_Logs\\Igby_Sample_Project_Log.txt",
    "PRE_RUN_PYTHON_COMMAND":"sample_pre_run_command.run()",
    "MIN_WAIT_SEC":60,
    "MAX_RUNS":1,
    "P4_PORT":"0.0.0.0:1666",
    "P4_USER":"user_name", 
    "P4_PASSWORD":"",
    "P4_CLIENT":"user_DESKTOP-F4B2F5M_6315",
    "P4_CL_DESCRIPTION_PREFIX":"#Igby Automation",
    "P4_DIRS_TO_SYNC":["D:\\Unreal Projects\\Sample_Project\\...","//depot/Project/...","//depot/Project/some_file.json"],
    "UE_CMD_EXE_PATH":"D:\\Epic Games\\UE_5.0\\Engine\\Binaries\\Win64\\UnrealEditor-Cmd.exe",
    "UE_PROJECT_PATH":"D:\\Unreal Projects\\Some_Project\\Some_Project.uproject",
    "UE_HALT_ON_ERROR":false,
    "FORCE_RUN":true,
    "MODULES_TO_RUN":[
        {"redirector_cleaner_S":{
            "PATHS_TO_INCLUDE":["/Game/"],
            "PATHS_TO_IGNORE":["/Game/Developers/"],
            "DELETE_REDIRECTORS":true,
            "SUBMIT_CHANGELIST":false
            }
        },
        {"dual_asset_package_report_R":{
            "PATHS_TO_INCLUDE":["/Game/"],
            "PATHS_TO_IGNORE":["/Game/Developers/"],
            "REPORT_PATH":["D:\\Sample_Project\\Igby_Reports\\"],
            "KEEP_PREVIOUS_REPORTS":false
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

Igby V0.1.0 tested with the following setup:\
Windows 10 Pro Version 10.0.19044 Build 19044\
Unreal Editor 4.27, 5.0.0\
Python 3.7.7, 3.9.7\
Perforce P4D/LINUX26X86_64/2021.2/2273812 (2022/04/14)

## What Are Modules?

Modules are unique scripts that you can choose to run on your project. Module description is provided at the top of each .py file.
Currently modules come in 2 varieties:
1. Modules that only read data to gather and display information will have an "R" at the end.
2. Modules that modify the assets and submit them into Perforce will have an "S" at the end.

## Included Modules: 

**asset_hard_reference_report_R** - This module generates a report of assets that have large dependency chains. Large dependency chains could cause slow loads and other complications. It is recommended to replace hard references with soft references that can be loaded on demand and even asynchronously.

**asset_with_prohibited_dependencies_report_R** - This module generates a report of assets that have dependencies in prohibited folders. For example you can identify assets outside of the developer folder that contain dependencies inside the developer folder.

**dual_asset_package_report_R** - This module generates a report of packages that contain more than one asset. Sometimes unreal generates packages with multiple assets. This does not occur often but could result in errors when certain operations are applied. Packages with multiple assets also result in multiple assets being locked up when one is being worked on. I recommend identifying such assets and splitting them up into individual packages when possible.

**redirector_cleaner_S** - This module was the inspiration for igby. It identifies redirectors and cleans referencing assets as they become available in perforce. Once the redirector doesn't have valid dependencies or referencers, the redirector gets deleted. Please be careful with this one as it actually changes assets.

**unused_assets_report_R** - This module identifies unused assets and presents them as a list. The resulting report can be used as guidance for which assets should be cleaned out from the project.

**blueprints_with_missing_parent_class_report_R** - This module identifies blueprints that are missing a parent class. These blueprints are likely in a broken state and can either be re-parented to an existing class or deleted.

(There are lots of useful modules planned so stay tuned!)

## Key Updates

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

