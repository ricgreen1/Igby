# Igby

Igby is an Unreal Engine CI Automation Platform.

Igby utilizes The Unreal Engine CLI and Perforce python library to continuously sync and run modules on UE project content. This system can be used to monitor as well as modify project assets.

It is written in python using unreal and perforce libraries. Using python provides complete source code transparency and enables a broader user base to utilize Igby as well as author additional modules for their needs.

My goal is to continue to work on Igby features/improvements as well as expansion of the Igby module library. So if you have any suggestions/requests or just want to say hi, please send me an email to rg.igby@gmail.com


Setup:

Igby is self contained and only requires 4 steps:
1. Copy the whole ignby folder to one of your local drives. Make sure it has ample storage space.
2. Create a dedicated Perforce user and clientspec.
3. Create a [igby_python] environment variable that points to the python executable that you want Igby to use.
4. Create a custom version of the included [sample_igby_settings.json] file to reflect your settings. More settings info in the "Settings" section below.


To Run:

(Windows) Drag your settings json file that contains the settings and drop it on igby.bat

(Cmd Shell) Provide the settings json file as the argument for igby.bat Ex. igby.bat my_project_settings.json

Including -d after the .json file will run igby with full verbosity for debugging purposes.


Info:

Igby V0.1.0 tested with the following setup:
Windows 10 Pro Version 10.0.19044 Build 19044
Unreal Editor 5.0.0
Python 3.9.7
Perforce P4D/LINUX26X86_64/2021.2/2273812 (2022/04/14)


Modules:

Module description is provided at the top of each .py file.
Currently modules come in 2 varieties:
1. Modules that only read data to gather and display information will have an "R" at the end.
2. Modules that modify the assets and submit them into Perforce will have an "S" at the end. These modules should only work with exclusive checkouts.


Settings:

Most settings are self explanatory with a few exceptions listed here.

"PRE_RUN_PYTHON_COMMAND" (This runs a python command before every Igby run. This might be a good place to make UE updates.)

"MIN_WAIT_SEC" (This is the minimum time in seconds Igby should wait between each run. This timer starts at the beginning of each run.)

"MAX_RUNS" (This is how many times you want Igby to run the modules. 0 = indefinitely)

"P4_PASSWORD" (If left blank Igby will prompt you for the Perforce password during the initial run.)

"P4_CL_DESCRIPTION_PREFIX" (This is the prefix in the changelist description that you want in every changelist that Igby generates.)

"UE_HALT_ON_ERROR" If this setting is set to true then Igby will halt if an error is detected.

"FORCE_RUN" Igby is designed to run the modules only if there is new data from perforce or if a pre-run command makes updates. Setting this to true will force run the modules every time.

Each module that you want to run should be included in the settings file with its corresponding settings as seen in the included sample sample_igby_settings.json file. The settings for each module can be seen in the beginning of the run() function of the module's .py file.
