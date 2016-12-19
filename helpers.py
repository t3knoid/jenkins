import os
import stat
import time
import os.path
import shutil
import sys
import win32wnet
from datetime import date
import hashlib
import subprocess

def hashfile(afile, hasher, blocksize=65536):
    """ Return an MD5 of the given file

    This generates the MD5 signature of given file
    """
    buf = afile.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = afile.read(blocksize)
    return hasher.digest()

# Convert DOS style path to Cygwin path
def dos2cygpath(dospath):
    """ Returns the Cygwin path equivalent of a given path.
    
    This method returns the Cygwin equivalent of a given path. The path
    may be a path to a folder or a file.
    """

    #print '[INFO] Convert ' + '"' + dospath + '"' + ' to cygwin path equivalent.'
    drive, path_and_file = os.path.splitdrive(dospath)
    if os.path.isfile(dospath):
        path , file = os.path.split(path_and_file)
        dospathtokens = path.split(os.sep)  # Split path into tokens
    else:
        dospathtokens = path_and_file.split(os.sep)
    dospathtokens.pop(0) # Remove first item in list because its blank
    cygpath = '/cygdrive/' + drive[0] + '/'
    for token in dospathtokens: 
        cygpath+=token
        cygpath+='/'
    try: # Append file if a path to a file was passed
        cygpath+=file  
    except NameError:
        #print '[INFO] no filename to append'
        sys.stdout.flush() 
    else:
        #print '[INFO] filename appended'
        sys.stdout.flush()
    #print '[INFO] returning cygpath = ' + cygpath
    sys.stdout.flush()
    return cygpath

def onerror(func, path, exc_info):
    """
    Error handler for ``shutil.rmtree``.

    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.

    If the error is for another reason it re-raises the error.
    
    Usage : ``shutil.rmtree(path, onerror=onerror)``
    """
    import stat
    if not os.access(path, os.W_OK):
        # Is the error an access error ?
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise

def hasfiles(dir):
    """ Returns True or False
    
    This is method  that determines if a given folder has files 
    or not. It returns true if a file is found in the given
    folder.
    """     
    for dirpath, dirnames, files in os.walk(dir):
        if files:
            return True
    return False

def upload_folder_flat(dest, folder, names):
    """ 
    Callback function for os.path.walk function that copies each file 
    in the given folder (folder) to the destination (dest) without
    retaining the source folder organization structure.
    """
    if hasfiles(folder):  # Perform operation if folder contains files
        print '[INFO] Copying files in folder ' + folder + ' to ' + dest + ' started.'
        sys.stdout.flush() 
        try:
            for file in names:
                scp(os.path.join(folder,file),dest)
        except OSError:
            print '[ERROR] Copying files in folder ' + folder + ' to ' + dest + ' failed.'
            sys.stdout.flush() 
        else:
            print '[INFO] Copying files in folder ' + folder + ' to ' + dest + ' successful.'
            sys.stdout.flush() 

def upload_app_pkg_to_docker_server(dest, folder, names):
    """ 
    This is a helper method to the os.walk.path function. It upload's the
    application package to the given SCP destination (dest). The app archive
    is enumerated by looking for a file that contains the string ms-appserver.
    """

    file = "".join([s for s in names if "ms-appserver".lower() in s.lower()])    # Search the list of filenames for the app server package
    scp(os.path.join(folder,file),dest)

def upload_web_pkg_to_docker_server(dest, folder, names):
    """
    This is a helper method to the os.walk.path function. It upload's the web 
    archive to the given SCP destination (dest). The web archive is enumerated
    by looking for the file that contains the string ms-webgui.
    """

    file = "".join([s for s in names if "ms-webgui".lower() in s.lower()])    # Search the list of filenames for the web server package
    scp(os.path.join(folder,file),dest)

def scp(file2copy,dest):
    """ Returns True or False
    This uses the external scp command (e.g. OPENSSH) to copy a given
    file (file2copy) to a given destination (dest). This method calls
    the helper method execute() to perform the actual execution of the
    scp command. Prior to calling scp, the file2copy is first converted
    to its Cygwin equivalent.
    """

    if not os.path.isfile(file2copy): # Work on files only
        return True
    print 'Copying ' + file2copy + ', please wait. ',
    sys.stdout.flush() 
    cygfilepath = dos2cygpath(file2copy) # Get cygwin equivalent path
    command = "scp " + "'" + cygfilepath + "' " + dest
    commandResult = execute(command)
    if commandResult == 0:
        print 'OK.'
        sys.stdout.flush() 
        return True
    else:
        print 'Failed.'   
        sys.stdout.flush() 
        return False

def execute(command):
    """ Returns the command's exit code. A return of 0 indicates sucessful.

    Execute's a given external command and prints the output of the command. It
    return's the command's return code. A return of 0 indicates successful.
    Otherwise, any other value is an indication of a failure.
    """
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    while True:     # Poll process for new output until finished
        nextline = process.stdout.readline()
        if nextline == '' and process.poll() is not None:
            break
        sys.stdout.write(nextline)
        sys.stdout.flush()

    output = process.communicate()[0]
    exitCode = process.returncode

    return exitCode
    #if (exitCode == 0):
    #    return output
    #else:
    #    raise ProcessException(command, exitCode, output)

def build_docker_images():
    """
    Launches the script that builds Docker images.
    """
    print 'Building Docker images'
    sys.stdout.flush() 
    command = "ssh jenkins@" + dockerbuildserver + " '" + "./checkssh.sh" + "'"
    execute(command)
