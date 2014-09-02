import os, sys, math, time, shutil, getopt
def isRootFolderThere(rootFolder):
    """
    Method used to check if root folder is valid or not
    """
    if not os.path.isdir(rootFolder):
        print 'No such root folder found.'
        return -1
    else:
        return 1
        
def findEmptyDirs(rootFolder = '', deleteFolder = False):
    """
    Used to find any empty folders wit the option to move these into a trash folder for quick deletion
    @param rootFolder: Path to root folder including the root folder name eg C:\Movies
    @type rootFolder: String
    """
    rootFolder = rootFolder
    if deleteFolder == 'False':
        deleteFolder = False
    else:
        deleteFolder = True
    ignoreDirNames      = ['.lacie', '$RECYCLE.BIN', '.mayaSwatches']
    brokenFolders       = []
    if isRootFolderThere(rootFolder = rootFolder):
        for eachChildDir in os.listdir(rootFolder):
            childPath = '%s/%s' % (rootFolder, eachChildDir)
            if os.path.isdir(childPath):
                print 'Scanning %s now' % childPath
                ignoreFileFolders   = []
                emptyFolders        = []
                for dirname, dirnames, filenames in os.walk(childPath):
                    for eachFile in filenames:
                        #print eachFile
                        if dirname.split('\\')[-1] not in ignoreDirNames:## Check for end folder name to make sure it isn't in our ignore list.
                            filePath = os.path.join(dirname, eachFile).replace('\\', '/')## yes yes just forcing it to this pathing cause I am sick ofthe mismatching
                            if not eachFile == "workspace.mel":
                                if os.path.dirname(filePath) not in ignoreFileFolders:
                                    ignoreFileFolders.extend([os.path.dirname(filePath)])
                                    
                for dirname, dirnames, filenames in os.walk(childPath):
                    for eachDir in dirnames:
                        dirPath = os.path.join(dirname, eachDir).replace('\\', '/')## yes yes just forcing it to this pathing cause I am sick ofthe mismatching
                        if dirPath not in emptyFolders:
                            try:
                                if not os.listdir(dirPath):
                                    emptyFolders.extend([dirPath])
                                if os.listdir(dirPath):
                                    if len(os.listdir(dirPath)) == 1 and 'workspace.mel' in os.listdir(dirPath):
                                        os.remove('%s/%s' % (dirPath, 'workspace.mel'))
                                        emptyFolders.extend([dirPath])
                            except WindowsError:
                                brokenFolders.extend([dirPath])
                                pass
                
                print '%s empty folders found' % len(emptyFolders)
                if deleteFolder:
                    for each in emptyFolders:
                        if each.split('\\')[-1] not in ignoreDirNames:
                            try:
                                os.removedirs(each)
                            except WindowsError:
                                pass
                    print '%s empty  folders removed.' % len(emptyFolders)
                print
    if brokenFolders:
        print 'Corrupt Folders found!'
        for each in brokenFolders:
            print each

def main(argv):
    path     = ''
    delete   = ''
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'p:d:')
    except getopt.GetoptError:
        print 'removeEmptyFolders.py -p <string> -d <boolean>'
        sys.exit(2)
    #print opts
    for opt, arg in opts:
        if opt == '-h':
            print 'removeEmptyFolders.py -p <string> -d <boolean>'
            sys.exit()
        elif opt in ("-p"):
            path = arg
        elif opt in ("-d"):
            delete = arg         
    

    start = time.time() 
    findEmptyDirs(path, delete)
    print 'Total time to remove empty folders: %s' % (time.time()-start)

    sys.exit(2)

if __name__ == "__main__":
   main(sys.argv[1:])