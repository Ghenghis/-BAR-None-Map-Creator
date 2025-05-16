
local mapinfo = {
    name        = "AI_Generated_Map-#002",
    shortname   = "AI_Generated_Map-#002",
    description = "AI generated terrain for Beyond All Reason",
    author      = "AI Map Generator",
    version     = "1",
    mapfile     = "maps/AI_Generated_Map-#002.smf",
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
    {x = 572.0, z = 1744.0},
    {x = 2836.0, z = 2312.0},
    {x = 1340.0, z = 840.0},
    {x = 2940.0, z = 1428.0},
    {x = 2572.0, z = 2792.0},
    {x = 2040.0, z = 1340.0},
    {x = 1316.0, z = 3144.0},
    {x = 2276.0, z = 3260.0},
    {x = 2340.0, z = 2120.0},
    {x = 704.0, z = 2288.0},
    {x = 2388.0, z = 1720.0},
    {x = 1128.0, z = 2752.0},
    {x = 1768.0, z = 3400.0},
    {x = 592.0, z = 1328.0},
    {x = 2628.0, z = 1116.0},
    {x = 2896.0, z = 1840.0},

}

return mapinfo
