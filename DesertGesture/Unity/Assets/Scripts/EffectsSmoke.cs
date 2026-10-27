using System.Collections;
using System.IO;
using UnityEngine;

public sealed class EffectsSmoke : MonoBehaviour
{
    IEnumerator Start()
    {
        yield return null;
        var game=GetComponent<DesertGame>();var effects=game.Effects;
        var visual=effects.GetComponent<SportsCarVisual>();
        effects.Apply(true,100);
        bool braking=effects.BrakeLit && effects.Smoking && visual.BrakeEmission>3;
        effects.Apply(true,0);
        bool stopped=effects.BrakeLit && !effects.Smoking;
        effects.Apply(false,100);
        bool released=!effects.BrakeLit && !effects.Smoking && visual.BrakeEmission<1;
        effects.Apply(true,100);game.ResetRun();
        bool reset=!effects.BrakeLit && !effects.Smoking && effects.LiveParticles==0;
        bool bounds=!DesertGame.Overlaps(0,0,6,6,1,2) && DesertGame.Overlaps(0,0,6,6,1.16f,5.1f)
            && !DesertGame.Overlaps(0,3.3f,0,0,1.16f,5.1f) && DesertGame.Overlaps(0,0,20,-20,1.13f,4);
        bool following=DesertGame.FollowingSpeed(25,14,2)<14 && DesertGame.FollowingSpeed(25,0,0)==0;
        bool fleet=true;
        foreach(TrafficVehicle.Kind type in System.Enum.GetValues(typeof(TrafficVehicle.Kind)))
        {
            var obj=new GameObject("Fleet verification");var car=obj.AddComponent<TrafficVehicle>();
            var material=new Material(Resources.Load<Material>("DesertBase"));car.Build(type,material);
            fleet &= car.GetComponentsInChildren<MeshRenderer>().Length>10 && car.HalfLength>=2 && car.Cruise>0;
            car.Animate(.016f,true);Destroy(obj);Destroy(material);
        }
        string result=$"braking={braking}; stopped_no_smoke={stopped}; release={released}; reset={reset}; vehicle_bounds={bounds}; following={following}; fleet={fleet}";
        Debug.Log("EFFECTS TEST: "+result);File.WriteAllText(Path.Combine(Application.dataPath,"../effects-test.txt"),result);
        Application.Quit(braking&&stopped&&released&&reset&&bounds&&following&&fleet?0:2);
    }
}
