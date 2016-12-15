import os
import stat
import os.path
import shutil
import sys
import win32wnet
from datetime import date
import hashlib

"""
# Generate MD5 signature of given file
# hashfile(open(fname, 'rb'), hashlib.md5())
def hashfile(afile, hasher, blocksize=65536):
    buf = afile.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = afile.read(blocksize)
    return hasher.digest()

# Convert DOS style path to Cygwin path
def dos2cygpath(dospath):
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

# Error handling
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

# Callback function for os.path.walk function. It copies each file in given folder
def copy2docker(dest, folder, names):
    for file in names:
        file2copy = os.path.join(folder, file)
        if os.path.isfile(file2copy ): # Work on files only
            cygfilepath = dos2cygpath(file2copy) # Get cygwin equivalent path
            #print "scp " + "'" + cygfilepath + "' " + dest
            try:
                os.system("scp " + "'" + cygfilepath + "' " + dest)
            except OSError:
                print '[ERROR] failed to copy ' + cygfilepath 
                sys.stdout.flush() 
            else:
                print 'Copy successful ' + cygfilepath
