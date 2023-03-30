# prerequisites_lib.py Igby UE Project Automator
# Developed by Richard Greenspan | igby.rg@gmail.com
# Licensed under the MIT license. See LICENSE file in the project root for details.

import igby_lib, sys, importlib

def pip_setup():

    lib_dir = igby_lib.get_lib_dir()
    sys.path.append(f"{lib_dir}/pip")

    try:
        import pip
    except ImportError:
        print("Pip not present. Commencing Pip installation.")
        
        try:
            import get_pip
            get_pip.main()
            import pip
        except:
            raise(Exception("Pip could not be installed."))
        
    print(f"pip verion:{pip.__version__}")
    
    return True
        

def setup_prerequisites(settings, logger):

    #install prerequisites

    lib_dir = igby_lib.get_lib_dir()

    if "PY_LIBS" in settings:

        logger.log("Setting up python library prerequisites:")

        py_libs = settings["PY_LIBS"]

        for py_lib in py_libs:

            lib_path = f"{lib_dir}/{py_lib}"
            sys.path.append(lib_path)

            try:

                importlib.import_module(py_libs[py_lib]["module"])

            except:

                install_package(py_lib, lib_path)

                try:
                    importlib.import_module(py_libs[py_lib]["module"])
                except:
                    raise(Exception(f"The following library could not be imported: {py_lib}"))
                
            logger.log(f"Python module ready: {py_libs[py_lib]['module']}")


def install_package(package, destination):

    if pip_setup():

        import pip

        if hasattr(pip, 'main'):
            pip.main(['install', '-t', destination, package])
        else:
            from pip._internal import main
            main(['install', '-t', destination, package])