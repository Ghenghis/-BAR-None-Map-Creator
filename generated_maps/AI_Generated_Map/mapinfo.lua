
local mapinfo = {
    name        = "AI_Generated_Map",
    shortname   = "AI_Generated_Map",
    description = "AI generated terrain for Beyond All Reason",
    author      = "AI Map Generator",
    version     = "1",
    mapfile     = "maps/AI_Generated_Map.smf",
    modtype     = 3, --// 1=primary, 0=hidden, 3=map
    depend      = {"Map Helper v1"},
    
    maphardness     = 100,
    notDeformable   = false,
    gravity         = 130,
    tidalStrength   = 0,
    maxMetal        = 0.02,
    extractorRadius = 500,
    
    smf = {
        minheight = 0,
        maxheight = 200,
    },
    
    resources = {
        resourceUnits = {
            metal = 1000,
            energy = 1000,
        },
    },
    
    splats = {
        texScales = {0.002, 0.002, 0.002, 0.002},
        texMults  = {1.0, 1.0, 1.0, 1.0},
    },
    
    atmosphere = {
        minWind      = 5,
        maxWind      = 25,
        fogStart     = 0.1,
        fogEnd       = 1.0,
        fogColor     = {0.7, 0.7, 0.8},
        skyColor     = {0.1, 0.15, 0.7},
        sunColor     = {1.0, 1.0, 0.9},
        cloudColor   = {0.9, 0.9, 0.9},
        cloudDensity = 0.5,
    },
    
    terrainTypes = {
        {
            name = "Default",
            texture = "default.png",
            texureScale = 0.02,
        },
    },
    
    custom = {
        fog = {
            color    = {0.26, 0.30, 0.41},
            height   = "80%",
            fogatten = 0.003,
        },
        precipitation = {
            density   = 30000,
            size      = 1.5,
            speed     = 50,
            windscale = 1.2,
            texture   = 'LuaGaia/Addons/snow.png',
        },
    },
}

-- Metal spot definitions
mapinfo.metalSpots = {
    {x = 384.0, z = 928.0},
    {x = 2156.0, z = 664.0},
    {x = 40.0, z = 164.0},
    {x = 3728.0, z = 992.0},
    {x = 3456.0, z = 468.0},
    {x = 1780.0, z = 996.0},
    {x = 24.0, z = 572.0},
    {x = 1400.0, z = 780.0},
    {x = 728.0, z = 1144.0},
    {x = 2740.0, z = 980.0},
    {x = 944.0, z = 496.0},
    {x = 3108.0, z = 800.0},

}

return mapinfo
