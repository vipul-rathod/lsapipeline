import os
def debug(app= '', method = '', message = '', verbose = False):
    """
    Function to help debug application messages from shotgun to turn them on or off quickly
    Also outputs a log regardless of verbose = True
    """
    if not app:
        if verbose:
            #print ('# Warning: Shotgun:  Method: %-45s %s' % (method, message))
            print '# Warning: Shotgun:  Method: {0:<15} {1}'.format(method, message)
        else:
            pass
    else:
        try:
            if verbose:
                if method == '':
                    app.log_warning(message)
                    #app.log_info(message)
                else:
                    app.log_warning('\nMethod:%-15s %s' % (method, message))
            else:
                pass
        except:
            print 'debug msg failed... app sent through okay?' 


    ### Write to temp log file regardless of debug setting
    pathToLog = r"C:\Temp\bbbayLog.txt"
    
    if not os.path.isfile(pathToLog):
        try:os.mkdir('C:\Temp')
        except:pass
        outfile = open(pathToLog, "w")
    else:
        outfile = open(pathToLog, "a")
    outfile.write('Method: %-15s %s\n' % (method, message))
    outfile.close()