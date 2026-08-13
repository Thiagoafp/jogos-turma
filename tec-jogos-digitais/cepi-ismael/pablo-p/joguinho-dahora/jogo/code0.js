gdjs.Cena_32sem_32t_237tuloCode = {};
gdjs.Cena_32sem_32t_237tuloCode.localVariables = [];
gdjs.Cena_32sem_32t_237tuloCode.idToCallbackMap = new Map();
gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects1= [];
gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects2= [];
gdjs.Cena_32sem_32t_237tuloCode.GDGround_9595TileObjects1= [];
gdjs.Cena_32sem_32t_237tuloCode.GDGround_9595TileObjects2= [];
gdjs.Cena_32sem_32t_237tuloCode.GDBoxesObjects1= [];
gdjs.Cena_32sem_32t_237tuloCode.GDBoxesObjects2= [];
gdjs.Cena_32sem_32t_237tuloCode.GDBarrelObjects1= [];
gdjs.Cena_32sem_32t_237tuloCode.GDBarrelObjects2= [];
gdjs.Cena_32sem_32t_237tuloCode.GDTileset_9595Piece_959514Objects1= [];
gdjs.Cena_32sem_32t_237tuloCode.GDTileset_9595Piece_959514Objects2= [];
gdjs.Cena_32sem_32t_237tuloCode.GDChemical_9595PotObjects1= [];
gdjs.Cena_32sem_32t_237tuloCode.GDChemical_9595PotObjects2= [];


gdjs.Cena_32sem_32t_237tuloCode.mapOfGDgdjs_9546Cena_959532sem_959532t_9595237tuloCode_9546GDChemical_95959595PotObjects1Objects = Hashtable.newFrom({"Chemical_Pot": gdjs.Cena_32sem_32t_237tuloCode.GDChemical_9595PotObjects1});
gdjs.Cena_32sem_32t_237tuloCode.mapOfGDgdjs_9546Cena_959532sem_959532t_9595237tuloCode_9546GDCyber_95959595PrisonerObjects1Objects = Hashtable.newFrom({"Cyber_Prisoner": gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects1});
gdjs.Cena_32sem_32t_237tuloCode.eventsList0 = function(runtimeScene) {

{

gdjs.copyArray(runtimeScene.getObjects("Cyber_Prisoner"), gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects1);

let isConditionTrue_0 = false;
isConditionTrue_0 = false;
for (var i = 0, k = 0, l = gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects1.length;i<l;++i) {
    if ( gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects1[i].getBehavior("PlatformerObject").isMovingEvenALittle() ) {
        isConditionTrue_0 = true;
        gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects1[k] = gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects1[i];
        ++k;
    }
}
gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects1.length = k;
if (isConditionTrue_0) {
/* Reuse gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects1 */
{for(var i = 0, len = gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects1.length ;i < len;++i) {
    gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects1[i].getBehavior("Animation").setAnimationName("Run");
}
}
}

}


{

gdjs.copyArray(runtimeScene.getObjects("Cyber_Prisoner"), gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects1);

let isConditionTrue_0 = false;
isConditionTrue_0 = false;
for (var i = 0, k = 0, l = gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects1.length;i<l;++i) {
    if ( !(gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects1[i].getBehavior("PlatformerObject").isMovingEvenALittle()) ) {
        isConditionTrue_0 = true;
        gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects1[k] = gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects1[i];
        ++k;
    }
}
gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects1.length = k;
if (isConditionTrue_0) {
/* Reuse gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects1 */
{for(var i = 0, len = gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects1.length ;i < len;++i) {
    gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects1[i].getBehavior("Animation").setAnimationName("Idle");
}
}
}

}


{

gdjs.copyArray(runtimeScene.getObjects("Cyber_Prisoner"), gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects1);

let isConditionTrue_0 = false;
isConditionTrue_0 = false;
for (var i = 0, k = 0, l = gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects1.length;i<l;++i) {
    if ( gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects1[i].getBehavior("PlatformerObject").isJumping() ) {
        isConditionTrue_0 = true;
        gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects1[k] = gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects1[i];
        ++k;
    }
}
gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects1.length = k;
if (isConditionTrue_0) {
/* Reuse gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects1 */
{for(var i = 0, len = gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects1.length ;i < len;++i) {
    gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects1[i].getBehavior("Animation").setAnimationName("Jump");
}
}
}

}


{

gdjs.copyArray(runtimeScene.getObjects("Chemical_Pot"), gdjs.Cena_32sem_32t_237tuloCode.GDChemical_9595PotObjects1);
gdjs.copyArray(runtimeScene.getObjects("Cyber_Prisoner"), gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects1);

let isConditionTrue_0 = false;
isConditionTrue_0 = false;
isConditionTrue_0 = gdjs.evtTools.object.hitBoxesCollisionTest(gdjs.Cena_32sem_32t_237tuloCode.mapOfGDgdjs_9546Cena_959532sem_959532t_9595237tuloCode_9546GDChemical_95959595PotObjects1Objects, gdjs.Cena_32sem_32t_237tuloCode.mapOfGDgdjs_9546Cena_959532sem_959532t_9595237tuloCode_9546GDCyber_95959595PrisonerObjects1Objects, false, runtimeScene, false);
if (isConditionTrue_0) {
/* Reuse gdjs.Cena_32sem_32t_237tuloCode.GDChemical_9595PotObjects1 */
{for(var i = 0, len = gdjs.Cena_32sem_32t_237tuloCode.GDChemical_9595PotObjects1.length ;i < len;++i) {
    gdjs.Cena_32sem_32t_237tuloCode.GDChemical_9595PotObjects1[i].deleteFromScene(runtimeScene);
}
}
}

}


};

gdjs.Cena_32sem_32t_237tuloCode.func = function(runtimeScene) {
runtimeScene.getOnceTriggers().startNewFrame();

gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects1.length = 0;
gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects2.length = 0;
gdjs.Cena_32sem_32t_237tuloCode.GDGround_9595TileObjects1.length = 0;
gdjs.Cena_32sem_32t_237tuloCode.GDGround_9595TileObjects2.length = 0;
gdjs.Cena_32sem_32t_237tuloCode.GDBoxesObjects1.length = 0;
gdjs.Cena_32sem_32t_237tuloCode.GDBoxesObjects2.length = 0;
gdjs.Cena_32sem_32t_237tuloCode.GDBarrelObjects1.length = 0;
gdjs.Cena_32sem_32t_237tuloCode.GDBarrelObjects2.length = 0;
gdjs.Cena_32sem_32t_237tuloCode.GDTileset_9595Piece_959514Objects1.length = 0;
gdjs.Cena_32sem_32t_237tuloCode.GDTileset_9595Piece_959514Objects2.length = 0;
gdjs.Cena_32sem_32t_237tuloCode.GDChemical_9595PotObjects1.length = 0;
gdjs.Cena_32sem_32t_237tuloCode.GDChemical_9595PotObjects2.length = 0;

gdjs.Cena_32sem_32t_237tuloCode.eventsList0(runtimeScene);
gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects1.length = 0;
gdjs.Cena_32sem_32t_237tuloCode.GDCyber_9595PrisonerObjects2.length = 0;
gdjs.Cena_32sem_32t_237tuloCode.GDGround_9595TileObjects1.length = 0;
gdjs.Cena_32sem_32t_237tuloCode.GDGround_9595TileObjects2.length = 0;
gdjs.Cena_32sem_32t_237tuloCode.GDBoxesObjects1.length = 0;
gdjs.Cena_32sem_32t_237tuloCode.GDBoxesObjects2.length = 0;
gdjs.Cena_32sem_32t_237tuloCode.GDBarrelObjects1.length = 0;
gdjs.Cena_32sem_32t_237tuloCode.GDBarrelObjects2.length = 0;
gdjs.Cena_32sem_32t_237tuloCode.GDTileset_9595Piece_959514Objects1.length = 0;
gdjs.Cena_32sem_32t_237tuloCode.GDTileset_9595Piece_959514Objects2.length = 0;
gdjs.Cena_32sem_32t_237tuloCode.GDChemical_9595PotObjects1.length = 0;
gdjs.Cena_32sem_32t_237tuloCode.GDChemical_9595PotObjects2.length = 0;


return;

}

gdjs['Cena_32sem_32t_237tuloCode'] = gdjs.Cena_32sem_32t_237tuloCode;
