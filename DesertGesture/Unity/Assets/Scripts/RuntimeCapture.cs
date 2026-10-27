using System.Collections;
using System.IO;
using UnityEngine;

// Captures actual rendered gameplay for visual QA; only active with --capture.
public sealed class RuntimeCapture : MonoBehaviour
{
    IEnumerator Start()
    {
        yield return new WaitForSeconds(1);
        GetComponent<DesertGame>().StartRun();
        yield return new WaitForSeconds(6);
        ScreenCapture.CaptureScreenshot(Path.GetFullPath(Path.Combine(Application.dataPath,"../../preview.png")));
        yield return new WaitForSeconds(2);
        Application.Quit();
    }
}
