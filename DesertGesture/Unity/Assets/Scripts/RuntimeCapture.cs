using System.Collections;
using System.IO;
using UnityEngine;

// Captures actual rendered gameplay for visual QA; only active with --capture.
public sealed class RuntimeCapture : MonoBehaviour
{
    IEnumerator Start()
    {
        yield return new WaitForSeconds(1);
        bool traffic=System.Array.IndexOf(System.Environment.GetCommandLineArgs(),"--traffic-capture")>=0;
        if(traffic)GetComponent<DesertGame>().PrepareTrafficPreview();else GetComponent<DesertGame>().StartRun();
        yield return new WaitForSeconds(traffic?.4f:6);
        ScreenCapture.CaptureScreenshot(Path.GetFullPath(Path.Combine(Application.dataPath,"../../preview.png")));
        yield return new WaitForSeconds(2);
        Application.Quit();
    }
}
