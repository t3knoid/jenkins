import os
import stat
import time
import os.path
import shutil
import sys
import string
import win32wnet
from datetime import date
import hashlib
import subprocess

def md5(fname):
    """ Returns MD5 signature of given file
    This calculates the MD5 signature of a given file.
    """
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def verify_md5(fname):
    """ Returns true if the MD5 signature matches
    This verifies the md5 signature of a given file. The file 
    must be fully qualified. There must be an accoumpanying md5
    file that was calculated using the md5sum tool. 
    """
    printnflush("Calculating md5 signature of " + fname)
    calculated_md5=md5(fname)
    printnflush("Calculated md5 signature = " + calculated_md5)
    printnflush("Parsing stored md5 from " + fname  + ".md5")
    with open(fname + ".md5", 'r') as infile:
        first_line = infile.readline().split()
    stored_md5 = first_line[0].strip()
    printnflush("Stored md5 signature = " + stored_md5)
    if calculated_md5 == stored_md5:
       return True
    else:
       return False

def printnflush(msg):
   """ 
   This prints the given string and performs a flush immediately.
   """
   print(msg)
   sys.stdout.flush()

def dos2cygpath(dospath):
    """ Returns the Cygwin path equivalent of a given path.
    
    This method returns the Cygwin equivalent of a given path. The path
    may be a path to a folder or a file.
    """

    #printnflush '[INFO] Convert ' + '"' + dospath + '"' + ' to cygwin path equivalent.'
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

    # Try to append filename if it exists
    try:
        cygpath+=file
    except NameError:
        file = None

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
    
    This method determines if a given folder has files or not. 
    It returns true if a file is found in the given folder.
    """     
    for dirpath, dirnames, files in os.walk(dir):
        if len(files) > 0:
            return True
    return False

def create_softlinks(dir):
    """
    todo
    """

def upload_folder_flat(dest, folder, names):
    """ 
    Callback function for os.path.walk function that copies each file 
    in the given folder (folder) to the destination (dest) without
    retaining the source folder organization structure.
    """
    if hasfiles(folder):  # Perform operation if folder contains files
        printnflush('[INFO] Copying files in folder ' + folder + ' to ' + dest + ' started.')
        try:
            for file in names:
                file2copy = os.path.join(folder,file)
                if os.path.isfile(file2copy): # Work on files only
                   print 'Copying ' + file2copy + ', please wait. ',
                   cygfilepath = dos2cygpath(file2copy) # Get cygwin equivalent path
                   command = "scp" + " '" + cygfilepath + "' " + dest
                   execute(command)
        except OSError:
            printnflush('[ERROR] Copying files in folder ' + folder + ' to ' + dest + ' failed.')
        else:
            printnflush('[INFO] Copying files in folder ' + folder + ' to ' + dest + ' successful.')

def build_ui_docker_images(v,r,dest):
    """
    Launches the script that builds Docker ms ui image.
    """
    printnflush('Building Docker UI image build ' + v + '.' + r + '.')
    command = 'ssh ' + dest + ' "' + 'rm -fr ~/html/ms.zip' + '"'
    execute(command,True)
    command = 'ssh ' + dest + ' "' + 'mv ~/ms-webgui-' + v + '.zip ~/html/ms.zip' + '"'
    execute(command,True)
    command = 'ssh ' + dest + ' "' + 'rm -fr ~/images_ui/*' + '"'
    execute(command,True)
    command = 'ssh -t -t ' + dest + ' "' + 'sudo ./jenkins_build_ui.sh' + '"'
    execute(command,True)
    # Create MD5 files
    command = 'ssh -t -t ' + dest + ' "' + 'for f in ~/images_ui/*;do md5sum $f>${f}.md5;done' + '"'
    execute(command,True)

def build_app_docker_images(v,r,dest):
    """
    Launches the script that builds Docker ms app image.
    """
    printnflush('Building Docker App image build ' + v + '.' + r + '.')
    command = 'ssh ' + dest + ' "' + 'rm -fr ~/html/ms.war' + '"'
    execute(command,True)
    command = 'ssh ' + dest + ' "' + 'mv ~/ms-appserver-' + v + '.war ~/html/ms.war' + '"'
    execute(command,True)
    command = 'ssh ' + dest + ' "' + 'rm -fr ~/images_app/*' + '"'
    execute(command,True)
    command = 'ssh -t -t ' + dest + ' "' + 'sudo ./jenkins_build_app.sh' + '"'
    execute(command,True)
    # Create MD5 files
    command = 'ssh -t -t ' + dest + ' "' + 'for f in ~/images_app/*;do md5sum $f>${f}.md5;done' + '"'
    execute(command,True)

def stage_docker_builds(src,dest):
    """ 
    This copies the docker builds from the Docker server specified in
    src to the destination folder specified in dest.
    """
    printnflush('Staging Managed Services build to ' + dest)
    if os.path.exists(dest):   # Delete existing destination folder
       printnflush('Removing existing destination path, ' + dest)
       shutil.rmtree(dest,onerror=onerror)

    # Create destination folders
    printnflush('Creating destination folder, ' + dest)
    os.mkdir(dest)

    # Download application server image
    printnflush('Downloading application server image')
    sys.stdout.flush()
    command = "scp " + src + ":~/images_app/rhel7_edg_msd_app*.tar* '" + dest + "'"
    execute(command,True)    

    # Download web server image
    printnflush('Downloading web server image')
    command = "scp " + src + ":~/images_ui/rhel7_edg_msd_ui*.tar* '" + dest + "'"
    execute(command,True)    

def pretty_time(secs):
    """ Returns give time in seconds as h:m:s format
    This calculates a given time in seconds a string formatted in h:m:s
    """
    m, s = divmod(secs, 60)
    h, m = divmod(m, 60)
    pt = "%d:%02d:%02d" % (h, m, s)
    return pt

def execute(cmd,printcmd=False):
    """ Returns the command's exit code. A return of 0 indicates sucessful.

    Launches a given external command and prints the output of the command. It
    return's the command's return code. A return of 0 indicates successful.
    Otherwise, any other value is an indication of a failure.
    """
    if printcmd:
        printnflush(cmd)

    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    while True:     # Poll process for new output until finished
        nextline = process.stdout.readline()
        if nextline == '' and process.poll() is not None:
            break
        sys.stdout.write(nextline)
        sys.stdout.flush()

    output = process.communicate()[0]
    exitCode = process.returncode

    if (exitCode == 0):
        return output
    else:
        raise ProcessException(command, exitCode, output)

# Workspace
workspace = os.environ['WORKSPACE']        # Workspace root folder
jobname = os.environ['JOB_NAME']  # Job name
buildmachine = os.environ['NODE_NAME']     # Build server hostname
dockerbuildserver = os.environ['DOCKER_BUILD_SERVER'] # Docker build server
buildnumber = os.environ['PROMOTED_DISPLAY_NAME'] # Full build number including version and revision numbers
svnrevision = os.environ['SVN_REVISION'] # Revision number
version = os.environ['POM_VERSION'] # Version number

# Initialize Staging folder Destination (e.g. L:\Managed Services Docker Images\1.2.3)
stagingsubfolder = os.environ['STAGING_SUBFOLDER'] # Staging subfolder
host = 'devfs02' # SMB server
share = 'L' # SMB share
username = 'tde' # SMB user
password = 'etech' # SMB user password
unc = ''.join(['\\\\', host]) # UNC path
win32wnet.WNetAddConnection2(0, None, unc, None, username, password) # Connect to destination share
dockerimagestagingpath = unc + '\\' + share + '\\' + stagingsubfolder + '\\' + buildnumber

cygworkspace = dos2cygpath(workspace) # Convert workspace to Cygwin equivalent for use with scp command

# Tomcat config files artifact directory
appconfigdir = os.path.join(workspace, "configs")  
appconfigdir = os.path.join(appconfigdir, "tomcat")

# HTTPD config files artifact directory
httpdconfigdir = os.path.join(workspace , "configs")
httpdconfigdir = os.path.join(httpdconfigdir , "httpd")

# Application packages artifact directory (GUI and APP)
apptargetdir = os.path.join(workspace, "target")

# Docker build server connection
dockerconnection = "jenkins@" + dockerbuildserver

# Print info
printnflush('[INFO] Relevant properties')
printnflush('WORKSPACE  = ' + workspace)
printnflush('NODE_NAME = ' + buildmachine)
printnflush('STAGING_SUBFOLDER = ' + stagingsubfolder )
printnflush('DOCKER_BUILD_SERVER = ' + dockerbuildserver)
printnflush('DOCKER CONNECTION = ' + dockerconnection) 
printnflush('BUILD NUMBER = ' + buildnumber)
printnflush('VERSION NUMBER = ' + version)
printnflush('REVISION NUMBER = ' + svnrevision)
printnflush('DOCKER IMAGE STAGING PATH = ' + dockerimagestagingpath)
printnflush('CYGWIN WORKSPACE EQUIVALENT = ' + cygworkspace)
printnflush('HTTPD CONFIGURATION FOLDER = ' + httpdconfigdir)
printnflush('TOMCAT CONFIGURATION FOLDER = ' + appconfigdir)

# Copy UI config files to Docker build server
printnflush("[INFO] Copying UI config files to Docker build server")
start_time = time.time()
os.path.walk(httpdconfigdir, upload_folder_flat, dockerconnection + ":~/configs/ui")
elapsed_time = time.time() - start_time
printnflush("Copy time = " + pretty_time(elapsed_time))
# Copy App config files to Docker build server
printnflush("[INFO] Copying application config files to Docker build server")
start_time = time.time()
os.path.walk(appconfigdir, upload_folder_flat, dockerconnection + ":~/configs/app")
elapsed_time = time.time() - start_time
printnflush("Copy time = " + pretty_time(elapsed_time))

# Copy web and app build packages to Docker build server
printnflush("[INFO] Copying application build packages to Docker build server")
start_time = time.time()
os.path.walk(apptargetdir, upload_folder_flat, dockerconnection + ":~/")
elapsed_time = time.time() - start_time
printnflush("Copy time = " + pretty_time(elapsed_time))

# Execute Docker build scripts here
printnflush("[INFO] Building UI Docker images")
start_time = time.time()
build_ui_docker_images(version,svnrevision,dockerconnection)
elapsed_time = time.time() - start_time
printnflush("Execution time = " + pretty_time(elapsed_time))

printnflush("[INFO] Building App Docker images")
start_time = time.time()
build_app_docker_images(version,svnrevision,dockerconnection)
elapsed_time = time.time() - start_time
printnflush("Execution time = " + pretty_time(elapsed_time))

printnflush("[INFO] Staging Docker images")
start_time = time.time()
stage_docker_builds(dockerconnection,dockerimagestagingpath)
elapsed_time = time.time() - start_time
printnflush("Copy time = " + pretty_time(elapsed_time))

printnflush("[INFO] Getting md5 of staged builds")
start_time = time.time()
if verify_md5(os.path.join(dockerimagestagingpath, "rhel7_edg_msd_ui.tar")):
   printnflush("[INFO] MD5 verification OK")
else:
   printnflush("[ERROR] MD5 verification failed")
   sys.exit(-1)
elapsed_time = time.time() - start_time
printnflush("Copy time = " + pretty_time(elapsed_time))
sys.exit(0)
