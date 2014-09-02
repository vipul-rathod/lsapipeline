import getpass

WIN_RSYNCFILES                  = r'C:/Users/%s/Desktop/rsyncPaths' % getpass.getuser()
MAC_RSYNCFILES                  = r'/Users/%s/Desktop/rsyncPaths' % getpass.getuser()
WIN_TEMP_FOLDER                 = r"C:\Temp"
MAC_TEMP_FOLDER                 = r"/_development/Temp"


#######################################################################################
#### LEMONSKY AUDIO DAILIES
LSAUDIO_EPFOLDERIGNORES           = ['eptst', 'eptst2', 'epDR', 'training', 'eptst106', 'animation test audio march 04']
LSAUDIO_STEPSLABEL                = 'Audio Steps'
LSAUDIO_STEPS                     = ['ALL', 'WAV']
LSLSAUDIO_STEPSDEFAULTCHECKED       = ['WAV']
LSAUDIO_GLOBALSYSTEMIGNORES       = ['*.yml', '*.txt', '.lacie', '*.lnk', '.AppleDouble', 'reference', '.mayaSwatches', 'workspace.mel', '.DS_Store', 'autosave', 'Thumbs.db']
LSAUDIO_STEPFOLDERIGNORES         = ['animatic', 'editorial', 'AFX', 'AnmPub', 'fx']
LSAUDIO_WORKFOLDERINGORES         = ['oceanPresets', 'snapshots', 'sourceimages']
LSAUDIO_PUBLISHFOLDERIGNORES      = ['alembic', 'alembic_anim', 'alembic_static', 'cam', 'fluids', 'gpu', 'lightxml', 'maya', 'nuke', 'photoshop', 'xml',
                                   'softimage', 'houdini', 'artwork', 'footage', 'cache', 'images', 'snapshots', 'renderData', 'fx']
LSAUDIO_FILETYPEIGNORES           = ['*.xml', '*.mel']

LSAUDIO_WIN_DEFAULTSOURCE         = 'E:/lsapipeline/audios/'     
LSAUDIO_MAC_DEFAULTSOURCE         = '/_projects/lsapipeline/audios/'

LSAUDIO_LSKY_DEFAULTDEST          = 'I:/lsapipeline/audios/'
LSAUDIO_PPICS_DEFAULTDEST         = 'jamesd@120.150.180.153:/home/jamesd/IDrive/lsapipeline/episodes/'
LSAUDIO_WIN_LOCAL_DEFAULTDEST     = 'A:/lsapipeline/audios'
LSAUDIO_MAC_LOCAL_DEFAULTDEST     = '/_projects/lsapipeline/'

LSAUDIO_DEFAULTPORT               = 222
LSAUDIO_PPICSPORT                 = 22

#######################################################################################
#### AUDIO DAILIES
AUDIO_EPFOLDERIGNORES           = ['eptst', 'eptst2', 'epDR', 'training', 'eptst106', 'animation test audio march 04']
AUDIO_STEPSLABEL                = 'Audio Steps'
AUDIO_STEPS                     = ['ALL', 'WAV']
AUDIO_STEPSDEFAULTCHECKED       = ['WAV']
AUDIO_GLOBALSYSTEMIGNORES       = ['*.yml', '*.txt', '.lacie', '*.lnk', '.AppleDouble', 'reference', '.mayaSwatches', 'workspace.mel', '.DS_Store', 'autosave', 'Thumbs.db']
AUDIO_STEPFOLDERIGNORES         = ['animatic', 'editorial', 'AFX', 'AnmPub', 'fx']
AUDIO_WORKFOLDERINGORES         = ['oceanPresets', 'snapshots', 'sourceimages']
AUDIO_PUBLISHFOLDERIGNORES      = ['alembic', 'alembic_anim', 'alembic_static', 'cam', 'fluids', 'gpu', 'lightxml', 'maya', 'nuke', 'photoshop', 'xml',
                                   'softimage', 'houdini', 'artwork', 'footage', 'cache', 'images', 'snapshots', 'renderData', 'fx']
AUDIO_FILETYPEIGNORES           = ['*.xml', '*.mel']

AUDIO_WIN_DEFAULTSOURCE         = 'I:/lsapipeline/audios/'     
AUDIO_MAC_DEFAULTSOURCE         = '/_projects/lsapipeline/audios/'

AUDIO_LSKY_DEFAULTDEST          = 'Administrator@1.9.109.89:/home/Administrator/lsapipeline/audios/'
AUDIO_PPICS_DEFAULTDEST         = 'jamesd@120.150.180.153:/home/jamesd/IDrive/lsapipeline/episodes/'
AUDIO_WIN_LOCAL_DEFAULTDEST     = 'A:/lsapipeline/audios'
AUDIO_MAC_LOCAL_DEFAULTDEST     = '/_projects/lsapipeline/'

AUDIO_DEFAULTPORT               = 222
AUDIO_PPICSPORT                 = 22

#######################################################################################
#### ANIMATION DAILIES
ANIMATION_EPFOLDERIGNORES       = ['eptst', 'eptst2', 'epDR', 'training', 'eptst106']
ANIMATION_STEPSLABEL            = 'Animation Steps'
ANIMATION_STEPS                 = ['ALL', 'Anm', 'Blck', 'Comp', 'FX', 'Light', 'SBoard']
ANIMATION_STEPSDEFAULTCHECKED   = ['Anm']
ANIMATION_GLOBALSYSTEMIGNORES   = ['*.yml', '*.txt', '.lacie', '*.lnk', '.AppleDouble', 'reference', '.mayaSwatches', 'workspace.mel', '.DS_Store', 'autosave', 'Thumbs.db']
ANIMATION_STEPFOLDERIGNORES     = ['animatic', 'editorial', 'AFX', 'AnmPub', 'fx']
ANIMATION_WORKFOLDERINGORES     = ['oceanPresets', 'snapshots', 'sourceimages']
ANIMATION_PUBLISHFOLDERIGNORES  = ['alembic', 'alembic_anim', 'alembic_static', 'cam', 'fluids', 'gpu', 'lightxml', 'maya', 'nuke', 'photoshop', 'xml',
                                   'softimage', 'houdini', 'artwork', 'footage', 'cache', 'images', 'snapshots', 'renderData', 'fx']
ANIMATION_FILETYPEIGNORES       = ['*.ma', '*.mb', '*.xml', '*.mel']

ANIMATION_WIN_DEFAULTSOURCE     = 'I:/lsapipeline/episodes/'     
ANIMATION_MAC_DEFAULTSOURCE     = '/volumes/IDrive/lsapipeline/episodes'

ANIMATION_LSKY_DEFAULTDEST      = 'Administrator@1.9.109.89:/home/Administrator/lsapipeline/episodes/'
ANIMATION_PPICS_DEFAULTDEST     = 'jamesd@120.150.180.153:/home/jamesd/IDrive/lsapipeline/episodes/'
ANIMATION_WIN_LOCAL_DEFAULTDEST = 'A:/lsapipeline/episodes'
ANIMATION_MAC_LOCAL_DEFAULTDEST = '/_projects/lsapipeline/'

ANIMATION_DEFAULTPORT           = 222
ANIMATION_PPICSPORT             = 22

#######################################################################################
#### COMP DAILIES
COMP_EPFOLDERIGNORES            = ['RenderLayers', 'eptst', 'eptst2', 'epDR', 'training', 'eptst106', 'review', 'Shotgun', 'SequenceLoader', 'Sequence Loader', 'SquenceLoader', 'shotgun', 'New folder', 'shot gun'] 
COMP_STEPSLABEL                 = 'Animation Steps'
COMP_STEPS                      = ['ALL', 'Avid', 'review']
COMP_STEPSDEFAULTCHECKED        = ['review']
COMP_GLOBALSYSTEMIGNORES        = ['*.yml', '*.txt', '.lacie', '*.lnk', '.AppleDouble', 'reference', '.mayaSwatches', 'workspace.mel', '.DS_Store', 'autosave', 'Thumbs.db']
COMP_STEPFOLDERIGNORES          = ['editorial']
COMP_WORKFOLDERINGORES          = ['oceanPresets', 'snapshots', 'sourceimages']
COMP_PUBLISHFOLDERIGNORES       = ['quickdaily', 'RenderLayers', 'NukeWIPOutput', 'FxLayers']
COMP_FILETYPEIGNORES            = ['*.ma', '*.mb', '*.xml', '*.mel', '*.nk', '*.nk~', '*.ffs_db', '*.png', '*.nk.autosave', '*.exr', '*.png.tmp', '*.dpx', '*.iff']

COMP_WIN_DEFAULTSOURCE          = 'K:/lsapipeline/episodes/'     
COMP_MAC_DEFAULTSOURCE          = '/volumes/KDrive/lsapipeline/episodes'

COMP_LSKY_DEFAULTDEST           = 'Administrator@1.9.109.89:/home/Administrator/lsapipeline/episodes/'
COMP_PPICS_DEFAULTDEST          = 'jamesd@120.150.180.153:/home/jamesd/KDrive/lsapipeline/episodes/'
COMP_WIN_LOCAL_DEFAULTDEST      = 'A:/renders/lsapipeline/episodes'
COMP_MAC_LOCAL_DEFAULTDEST      = '/_renders/lsapipeline/'

COMP_DEFAULTPORT                = 222
COMP_PPICSPORT                  = 22

#######################################################################################
#### ASSET SYNC
ASSETS_EPFOLDERIGNORES          = [] 
ASSETS_STEPSLABEL               = 'Asset Steps'
ASSETS_STEPS                    = ['ALL', 'MDL', 'TXT', 'SRF', 'UV', 'DSN', 'RIG']
ASSETS_STEPSDEFAULTCHECKED      = ['MDL']
ASSETS_GLOBALSYSTEMIGNORES      = ['*.yml', '*.txt', '.lacie', '*.lnk', '.AppleDouble', 'reference', '.mayaSwatches', 'workspace.mel', '.DS_Store', 'autosave', 'Thumbs.db']
ASSETS_STEPFOLDERIGNORES        = ['editorial']
ASSETS_WORKFOLDERINGORES        = ['snapshots']
ASSETS_PUBLISHFOLDERIGNORES     = ['quickdaily', 'RenderLayers', 'NukeWIPOutput', 'FxLayers']
ASSETS_FILETYPEIGNORES          = ['*.nk', '*.nk~', '*.ffs_db', '*.nk.autosave', '*.exr', '*.png.tmp', '*.dpx']

ASSETS_WIN_DEFAULTSOURCE        = 'I:/lsapipeline/assets/'     
ASSETS_MAC_DEFAULTSOURCE        = '/volumes/IDrive/lsapipeline/assets'

ASSETS_LSKY_DEFAULTDEST         = 'Administrator@1.9.109.89:/home/Administrator/lsapipeline/'
ASSETS_PPICS_DEFAULTDEST        = 'jamesd@120.150.180.153:/home/jamesd/IDrive/lsapipeline/assets/'
ASSETS_WIN_LOCAL_DEFAULTDEST    = 'A:/lsapipeline/assets/'
ASSETS_MAC_LOCAL_DEFAULTDEST    = '/_projects/lsapipeline/'

ASSETS_DEFAULTPORT              = 222
ASSETS_PPICSPORT                = 22
