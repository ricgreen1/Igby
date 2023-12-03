# ue_general_lib.py asset helper functions for Igby UE Project Automator
# Developed by Richard Greenspan | rg.igby@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import unreal, os

def get_engine_version():
    
    engine_version = unreal.SystemLibrary.get_engine_version()
    engine_version_parts = engine_version.split(".")
    major = int(engine_version_parts[0])
    minor = int(engine_version_parts[1])
    patch = int(engine_version_parts[2])

    return [major, minor, patch]