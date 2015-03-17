/* 
   SVNRootChoice.groovy

   This script enumerates the SVN roots to be presented to the user. It assumes that all branches are 
   located in the "/branches/" subfolder and the trunk is located under the "/trunk/" subfolder. The 
   script uses the svn list command to enumerate all the branches. The trunk is added at the end of 
   the branches enumeration. The svn list output is formatted as XML. The XML is parsed using the 
   XmlSlurper library.
   
   This script is useful if you need to provide a dynamic list of SVN roots to choose from for your Jenkins job.
/*

svnUser = "" // Specify SVN user
svnPassword = "" // Specify SVN password
svnURL = "" // Specify SVN root folder
// Use svn list command to enumerate branches
svnCommand = ["svn","list","--username",svnUser,"--password",svnPassword,"--xml",svnURL + "/branches/"]
def proc = svnCommand.execute()
def xmlOutput = proc.in.text
def listXML = new XmlSlurper().parseText(xmlOutput) // Parse XML output
def list = listXML.list // Get list of branches from output
def svnroot=[] // This list will hold final list of SVN roots
list.entry.name.each{svnroot.add(svnURL + "/branches/" + it.text())} // Build SVN root list
svnroot.add(svnURL + "/trunk") // Add trunk to the list
svnroot // Show the list
