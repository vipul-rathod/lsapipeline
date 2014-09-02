import getpass

## PARTICLE SPRITES
TEXTUREPATH                 = "I:/lsapipeline/fx/sprites/water/water_gloop_3.tga"

## PARTICLE SHADER PRESETS
PARTICLE_CLOUD_SHADER       = r'I:/lsapipeline/fx/presets/particleCloud/particleCloud1.mel'
PARTICLE_CLOUD_MA_PATH      = r'I:/lsapipeline/fx/sprites/mist/mist_particleCloud_shader.ma'

## MAYA OCEAN PRESET STUFF
OCEANDISPSHADER             = 'ocean_dispShader'
OCEANANIMSHADER             = 'ocean_animShader'
OCEANINTERACTIVESHADER      = 'ocean_interactiveShader'
OCEAN_ANIM_PREVIEWPLANENAME = 'animPreviewPlane_prv'
OCEAN_INTERACTIVE_PREVIEWPLANENAME = 'interactivePreviewPlane_prv'

OCEANTEXTURE_PRESETPATH     = 'I:/lsapipeline/fx/presets/ocean'
OCEAN_RENDER_PRESETPATH     = 'I:/lsapipeline/fx/presets/Lighting'
OCEAN_RENDER_SHADER_MA      = 'oceanWaterRenderSHD'
MC_WATERSHD_NAME            = "oceanWater_cMia_shd"

## DEFINE FLUID TEXTURE STUFF
FOAM_FLUID_SHAPENODE        = 'oceanWakeFoamTextureShape'
WAKE_FLUID_SHAPENODE        = 'oceanWakeTextureShape'
INTERACTIVE_WAKE_FLUID_SHAPENODE        = 'interactive_oceanWakeTextureShape'
INTERACTIVE_FOAM_FLUID_SHAPENODE        = 'interactive_oceanWakeFoamTextureShape'

FLUID_EMITTER_PRESETPATH    = 'I:/lsapipeline/fx/presets/fluidEmitter'
OCEAN_FOAMTEXTURE_PRESET    = "/newOceanWakeFoamTexture.mel"
OCEAN_WAKETEXTURE_PRESET    = "/newOceanWakeTexture.mel"

## EMITTER PRESETS
EMITTERBASEPRESETPATH       = r"I:/lsapipeline/fx/presets/nEmitter"
REAREMITTERPRESETPATH       = r"I:/lsapipeline/fx/presets/nEmitter/RearEmitterSplash.mel"
SIDEEMITTERPRESETPATH       = r"I:/lsapipeline/fx/presets/nEmitter/SideEmitterSplash.mel"

## PARTICLE PRESETS
REARPARTICLEPRESETPATH      = r"I:/lsapipeline/fx/presets/nParticle/nParticleSplash.mel"
SIDEPARTICLEPRESETPATH      = r"I:/lsapipeline/fx/presets/nParticle/SidenParticleSplash.mel"
NPART_PRESETPATH            = r'I:/lsapipeline/fx/presets/nparticle'

## OTHER DYNAMIC PRESETS
FXNUCLEUSPRESETPATH         = r"I:/lsapipeline/fx/presets/nucleus/fxNucleus.mel"
RADIAL_PRESETPATH           = r'I:/lsapipeline/fx/presets/radialField'

## File Archiving
PATHTOPATHSTEXTFILE         = r'I:/lsapipeline/remote/archives/%s_paths.txt' % getpass.getuser()
BATPATH                     = r'I:\lsapipeline\remote\archives'
BATFILENAME                 = r'%s_tempArchive.bat' % getpass.getuser()
RENDERPATH                  = r'I:\lsapipeline\remote\archives'

## For the new ocean Hook setup
ANIMBATCHNAME               = '%s_animCacheExport.bat' % getpass.getuser()
FXBATCHNAME                 = '%s_FXCacheExport.bat' % getpass.getuser()
CTMP                        = r'C:\Temp'
PATHTOANIMBAT               = r'%s\%s' % (CTMP, ANIMBATCHNAME)
PATHTOFXBAT                 = r'%s\%s' % (CTMP, FXBATCHNAME)


## Generic stuff
CHARNAMESLIST               = ['Sydney', 'Terry', 'Zip', 'Muddles', 'Bonita', 'Cleo', 'Stormy']