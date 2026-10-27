using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class BuildProject
{
    [MenuItem("Desert Signal/Create demo scene")]
    public static void Setup()
    {
        Directory.CreateDirectory("Assets/Scenes");
        Directory.CreateDirectory("Assets/Resources");
        // Runtime-only Shader.Find references can be stripped from a player build.
        if(AssetDatabase.LoadAssetAtPath<Material>("Assets/Resources/DesertBase.mat")==null)
            AssetDatabase.CreateAsset(new Material(Shader.Find("Standard")),"Assets/Resources/DesertBase.mat");
        if(AssetDatabase.LoadAssetAtPath<Material>("Assets/Resources/DesertSky.mat")==null)
        {
            var sky=new Material(Shader.Find("Skybox/Procedural"));
            sky.SetColor("_SkyTint",new Color(.55f,.65f,.75f));sky.SetFloat("_AtmosphereThickness",.8f);sky.SetFloat("_Exposure",1.1f);
            AssetDatabase.CreateAsset(sky,"Assets/Resources/DesertSky.mat");
        }
        var scene=File.Exists("Assets/Scenes/Desert.unity")
            ? EditorSceneManager.OpenScene("Assets/Scenes/Desert.unity",OpenSceneMode.Single)
            : EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
        if(Object.FindFirstObjectByType<DesertGame>()==null)new GameObject("Desert Signal").AddComponent<DesertGame>();
        RenderSettings.fog=true;RenderSettings.fogMode=FogMode.ExponentialSquared;
        EditorSceneManager.SaveScene(scene,"Assets/Scenes/Desert.unity");
        EditorBuildSettings.scenes=new[]{new EditorBuildSettingsScene("Assets/Scenes/Desert.unity",true)};
        PlayerSettings.companyName="Gesture Lab";PlayerSettings.productName="Desert Signal";
        PlayerSettings.defaultScreenWidth=1280;PlayerSettings.defaultScreenHeight=720;
        PlayerSettings.fullScreenMode=FullScreenMode.Windowed;PlayerSettings.runInBackground=true;
        PlayerSettings.SetScriptingBackend(UnityEditor.Build.NamedBuildTarget.Standalone,ScriptingImplementation.Mono2x);
        AssetDatabase.SaveAssets();
    }
    public static void Build()
    {
        Setup();
        var path=Path.GetFullPath("../Build/DesertSignal.exe");Directory.CreateDirectory(Path.GetDirectoryName(path));
        var report=BuildPipeline.BuildPlayer(EditorBuildSettings.scenes,path,BuildTarget.StandaloneWindows64,BuildOptions.None);
        if(report.summary.result!=UnityEditor.Build.Reporting.BuildResult.Succeeded)throw new System.Exception("Build failed: "+report.summary.result);
    }
}
