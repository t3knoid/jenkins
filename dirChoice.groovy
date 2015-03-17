/*
  dirChoice.groovy
  
  Loops through a given root directory and displays the subdirectory entries as a list of choices. This
  can be used to provide a choice of folders in a parameterized build.
  
  The main gist of the code is the dir.eachFile loop. Inside the loop is where each folder name is
  pre-processed before adding into the list. In this example, we want to show a list of versions of 
  the application. The folder name contains the version of the application which will be parsed out
  and added to the list.
*/

import groovy.io.FileType

def builds = []
def versions = []

def dir = new File("\\\\devfs02\\L\\Hotshot Project Manager Release") // Define root folder

dir.eachFile (FileType.DIRECTORIES) { 
   // Pre-process each folder here before adding to the list. In this example, each folder is assumed 
   // to have the following moniker 2015-03-14 v 4.3.0.15370 Daily.
   if  (!it.name.startsWith('_')) { // Ignores any folder that starts with a "_"
     // Parse out version number
     def (deploydate, suffix) = it.name.split(' v ') // Splits the folder name
     def (version) = suffix.split(' ',2) // Version now holds the version number
     // Add the version to the list
     versions.add(version)
     versions.sort() // Sort the list
     versions.reverse(true)
   }
}
versions // Show the list
