using System;
using System.Collections;
using System.IO;
using UnityEngine;

// Enabled only by explicit --smoke flag; validates the built player and real UDP receiver.
public sealed class RuntimeSmoke : MonoBehaviour
{
    IEnumerator Start()
    {
        var g=GetComponent<DesertGame>();var r=GetComponent<GestureReceiver>();
        yield return null;
        bool mechanics=g.State==DesertGame.Phase.Ready;
        g.StartRun();g.ChangeLane(-1);g.ChangeLane(-1);mechanics &= g.Lane==0;
        g.ChangeLane(1);g.ChangeLane(1);g.ChangeLane(1);mechanics &= g.Lane==2;
        g.StepSpeed(10,false,true);mechanics &= Mathf.Approximately(g.Speed,145);
        g.StepSpeed(10,true,true);mechanics &= Mathf.Approximately(g.Speed,0);
        g.Crash();mechanics &= g.State==DesertGame.Phase.Crashed;
        g.ResetRun();mechanics &= g.Lane==1 && g.Score==0;
        mechanics &= DesertGame.Overlaps(0,0,10,-10) && !DesertGame.Overlaps(0,3.3f,10,-10);
        bool[] seen=new bool[5];string[] names={"UNKNOWN","LEFT","RIGHT","PALM","FIST"};
        float end=Time.realtimeSinceStartup+14;
        while(Time.realtimeSinceStartup<end)
        {
            if(r.Connected){int i=Array.IndexOf(names,r.Gesture);if(i>=0)seen[i]=true;}
            yield return null;
        }
        bool transport=Array.TrueForAll(seen,v=>v);
        // Sender finishes after 12 seconds; timeout must clear its last command.
        bool timeout=!r.Connected && r.Gesture=="UNKNOWN";
        string result=$"mechanics={mechanics}; udp_all_gestures={transport}; stale_timeout={timeout}";
        Debug.Log("SMOKE: "+result);
        File.WriteAllText(Path.Combine(Application.dataPath,"../smoke-result.txt"),result);
        Application.Quit(mechanics&&transport&&timeout?0:2);
    }
}
