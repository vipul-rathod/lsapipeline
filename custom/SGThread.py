## ---- SHOTGUN THREAD
#[ShotgunData]
#base_url=https://bubblebathbay.shotgunstudio.com/
#script_name=Toolkit
#api_key=0e756aa3d9dfc19839a5b3b1da8a14e4e2cdd5d8

import threading

class ThreadedConnection(threading.Thread):
    def __init__(self):
        self.SERVER_PATH     = 'https://bubblebathbay.shotgunstudio.com/' 
        self.SCRIPT_NAME     = 'Toolkit'     
        self.SCRIPT_KEY      = '0e756aa3d9dfc19839a5b3b1da8a14e4e2cdd5d8'
        self.sg              = None
        self.run()

    def run(self):
        try:
            print "Connecting to %s..." %(self.SERVER_PATH)
            self.sg = Shotgun(self.SERVER_PATH, self.SCRIPT_NAME, self.SCRIPT_KEY)
        except Exception, e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print "Unable to connect to Shotgun server. " + str(e)
            return
    
    def __getitem__(self):
        return self.sg