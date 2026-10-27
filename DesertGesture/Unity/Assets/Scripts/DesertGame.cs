using System.Collections.Generic;
using UnityEngine;

public sealed class DesertGame : MonoBehaviour
{
    public enum Phase { Ready, Driving, Paused, Crashed }
    public Phase State { get; private set; }
    public float Speed { get; private set; }
    public float Distance { get; private set; }
    public int Lane { get; private set; } = 1;
    public int Score => Mathf.FloorToInt(Distance * 10) + passed * 100;
    public GestureReceiver receiver;
    [Tooltip("Optional visual prefab only. Forward +Z, centered at road level, about 1.8 x 4 metres.")]
    public GameObject playerVisualPrefab, trafficVisualPrefab;
    Transform player;
    Camera chase;
    readonly List<Transform> scenery = new List<Transform>();
    readonly List<TrafficVehicle> traffic = new List<TrafficVehicle>();
    public VehicleEffects Effects {get;private set;}
    int trafficSequence;
    bool braking, captureBrake;
    readonly Dictionary<Color,Material> materials = new Dictionary<Color,Material>();
    float spawnTimer, crashFlash, gestureReleased;
    int passed;
    string heldSteer = "UNKNOWN";
    bool keyboardOnly;
    GUIStyle small, large, title;
    Material asphalt, sand, white, cyan, dark, stone;
    AudioSource audioSource;
    AudioClip crashSound;

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void Boot()
    {
        if (FindFirstObjectByType<DesertGame>() == null) new GameObject("Desert Signal").AddComponent<DesertGame>();
    }
    void Awake()
    {
        Application.targetFrameRate = 60;
        receiver = gameObject.AddComponent<GestureReceiver>();
        asphalt = Mat(new Color(.055f,.071f,.09f)); sand = Mat(new Color(.73f,.40f,.23f));
        white = Mat(new Color(.92f,.84f,.65f)); cyan = Mat(new Color(.05f,.9f,.9f), true);
        dark = Mat(new Color(.025f,.04f,.06f)); stone = Mat(new Color(.46f,.22f,.16f));
        RenderSettings.fog = true; RenderSettings.fogColor = new Color(.82f,.62f,.45f);
        RenderSettings.fogMode = FogMode.ExponentialSquared; RenderSettings.fogDensity = .006f;
        RenderSettings.ambientLight = new Color(.63f,.64f,.66f);
        RenderSettings.skybox = Resources.Load<Material>("DesertSky");
        var sun = new GameObject("Late afternoon sun").AddComponent<Light>();
        sun.type = LightType.Directional; sun.intensity = 1.5f; sun.color = new Color(1,.83f,.65f);
        sun.shadows = LightShadows.Soft; sun.transform.rotation = Quaternion.Euler(38,-35,0);
        foreach (var cam in FindObjectsByType<Camera>(FindObjectsSortMode.None)) cam.enabled = false;
        chase = new GameObject("Chase Camera").AddComponent<Camera>();
        chase.backgroundColor = new Color(.63f,.73f,.76f); chase.clearFlags = CameraClearFlags.Skybox;
        chase.farClipPlane = 420; chase.fieldOfView = 63;
        chase.transform.position = new Vector3(0,5,-9); chase.transform.rotation = Quaternion.Euler(17,0,0);
        if (FindFirstObjectByType<AudioListener>() == null) chase.gameObject.AddComponent<AudioListener>();
        Box("Desert floor", new Vector3(0,-.25f,150), new Vector3(800,.4f,800), sand);
        Box("Asphalt", new Vector3(0,-.025f,150), new Vector3(11,.12f,440), asphalt);
        for (int side = -1; side <= 1; side += 2)
        {
            Box("Road edge", new Vector3(side*5.3f,.05f,150), new Vector3(.12f,.025f,440), white);
            Box("Shoulder", new Vector3(side*5.8f,0,150), new Vector3(.6f,.08f,440), stone);
        }
        Random.InitState(49);
        for (int i=0; i<44; i++)
        {
            var chunk = new GameObject("Road scenery " + i).transform;
            chunk.position = new Vector3(0,0,i*10-30); scenery.Add(chunk);
            foreach (float x in new[]{-1.65f,1.65f}) Part(chunk,"Lane stripe", new Vector3(x,.05f,0), new Vector3(.10f,.025f,4), white);
            for (int side=-1;side<=1;side+=2)
            {
                Part(chunk,"Reflector",new Vector3(side*6.2f,.5f,0),new Vector3(.13f,1,.13f),dark);
                Part(chunk,"Signal",new Vector3(side*6.2f,1,0),new Vector3(.17f,.15f,.17f),cyan);
                float x=side*Random.Range(14f,70f), h=Random.Range(3f,16f);
                var rock=Part(chunk,"Sandstone mesa",new Vector3(x,h*.45f,0),new Vector3(Random.Range(5f,15f),h,Random.Range(6f,14f)),i%2==0?sand:stone);
                rock.gameObject.GetComponent<MeshFilter>().sharedMesh=MesaMesh();
                rock.rotation=Quaternion.Euler(Random.Range(-8,8),Random.Range(0,180),Random.Range(-8,8));
                if (i%3==0)
                {
                    var cactus = Mat(new Color(.16f,.27f,.22f));
                    Part(chunk,"Cactus trunk",new Vector3(side*9,1.2f,3),new Vector3(.35f,2.4f,.35f),cactus);
                    Part(chunk,"Cactus arm",new Vector3(side*9+.4f,1.6f,3),new Vector3(1,.25f,.3f),cactus);
                    Part(chunk,"Cactus tip",new Vector3(side*9+.8f,1.9f,3),new Vector3(.3f,.8f,.3f),cactus);
                }
            }
        }
        player = Car("Player", Mat(new Color(1f,.24f,.015f)), playerVisualPrefab);
        Effects=player.gameObject.AddComponent<VehicleEffects>();
        audioSource = gameObject.AddComponent<AudioSource>();
        crashSound = AudioClip.Create("Procedural crash", 11025,1,22050,false);
        var samples=new float[11025];
        for(int i=0;i<samples.Length;i++) samples[i]=Random.Range(-1f,1f)*Mathf.Pow(1f-i/(float)samples.Length,3)*.4f;
        crashSound.SetData(samples,0);
        ResetRun();
        if (System.Array.IndexOf(System.Environment.GetCommandLineArgs(), "--effects-test") >= 0) gameObject.AddComponent<EffectsSmoke>();
        if (System.Array.IndexOf(System.Environment.GetCommandLineArgs(), "--smoke") >= 0) gameObject.AddComponent<RuntimeSmoke>();
        if (System.Array.IndexOf(System.Environment.GetCommandLineArgs(), "--capture") >= 0 || System.Array.IndexOf(System.Environment.GetCommandLineArgs(), "--traffic-capture") >= 0) gameObject.AddComponent<RuntimeCapture>();
    }
    Material Mat(Color color, bool glow=false)
    {
        if(materials.TryGetValue(color,out var cached))return cached;
        var template=Resources.Load<Material>("DesertBase");
        var m=template!=null?new Material(template):new Material(Shader.Find("Standard")); m.color=color; m.SetFloat("_Glossiness",.35f);
        if(glow){m.EnableKeyword("_EMISSION");m.SetColor("_EmissionColor",color*.8f);} materials.Add(color,m);return m;
    }
    Transform Box(string name,Vector3 position,Vector3 scale,Material material)
    {
        var g=GameObject.CreatePrimitive(PrimitiveType.Cube);g.name=name;g.transform.position=position;g.transform.localScale=scale;
        g.GetComponent<Renderer>().sharedMaterial=material;Destroy(g.GetComponent<Collider>());return g.transform;
    }
    Transform Part(Transform parent,string name,Vector3 position,Vector3 scale,Material material)
    {var t=Box(name,Vector3.zero,scale,material);t.SetParent(parent,false);t.localPosition=position;return t;}
    Mesh MesaMesh()
    {
        // Flat-shaded, tapered sandstone; unit bounds so scene scale remains swappable.
        var vertices=new List<Vector3>();var triangles=new List<int>();
        int sides=7;var rings=new Vector3[3,sides];
        for(int level=0;level<3;level++)for(int i=0;i<sides;i++)
        {
            float angle=i*Mathf.PI*2/sides;
            float radius=(level==0?.58f:level==1?.48f:.32f)*Random.Range(.85f,1.12f);
            rings[level,i]=new Vector3(Mathf.Cos(angle)*radius,level==0?-.5f:level==1?.18f:.5f,Mathf.Sin(angle)*radius);
        }
        System.Action<Vector3,Vector3,Vector3> tri=(a,b,c)=>{int n=vertices.Count;vertices.Add(a);vertices.Add(b);vertices.Add(c);triangles.Add(n);triangles.Add(n+1);triangles.Add(n+2);};
        for(int i=0;i<sides;i++)
        {
            int next=(i+1)%sides;
            for(int l=0;l<2;l++){tri(rings[l,i],rings[l+1,i],rings[l,next]);tri(rings[l,next],rings[l+1,i],rings[l+1,next]);}
            tri(rings[2,i],new Vector3(0,.5f,0),rings[2,next]);
        }
        var mesh=new Mesh{name="Procedural sandstone"};mesh.SetVertices(vertices);mesh.SetTriangles(triangles,0);mesh.RecalculateNormals();mesh.RecalculateBounds();return mesh;
    }
    Transform Car(string name,Material paint,GameObject prefab)
    {
        var root=new GameObject(name).transform;
        if(prefab!=null){Instantiate(prefab,root);return root;}
        SportsCarVisual.Create(root,paint);
        return root;
    }
    public void ResetRun()
    {
        foreach(var t in traffic) Destroy(t.gameObject);traffic.Clear();
        braking=false;captureBrake=false;trafficSequence=0;Effects.Apply(false,0,false);
        Lane=1;Speed=0;Distance=0;passed=0;spawnTimer=1.5f;State=Phase.Ready;
        heldSteer="UNKNOWN";gestureReleased=0;player.position=Vector3.zero;player.rotation=Quaternion.identity;
    }
    public void StartRun(){if(State==Phase.Ready)State=Phase.Driving;}
    public void ChangeLane(int direction){if(State==Phase.Driving)Lane=Mathf.Clamp(Lane+direction,0,2);}
    public void Crash(){if(State!=Phase.Driving)return;State=Phase.Crashed;braking=false;Effects.Apply(false,0,false);Speed=0;crashFlash=1;audioSource.PlayOneShot(crashSound);}
    public static bool Overlaps(float playerX,float trafficX,float oldZ,float newZ,float halfWidth=.82f,float halfLength=1.6f)
    {float length=2+halfLength;return Mathf.Abs(trafficX-playerX)<.83f+halfWidth && Mathf.Min(oldZ,newZ)<length && Mathf.Max(oldZ,newZ)>-length;}
    public void StepSpeed(float dt, bool brake, bool boost)
    {Speed=Mathf.MoveTowards(Speed,brake?0:boost?145:85,(brake?95:35)*dt);}
    void Update()
    {
        float dt=Mathf.Min(Time.deltaTime,.05f);crashFlash=Mathf.Max(0,crashFlash-dt*1.7f);
        if(Input.GetKeyDown(KeyCode.K))keyboardOnly=!keyboardOnly;
        string g=keyboardOnly?"UNKNOWN":receiver.Gesture;
        if(Input.GetKeyDown(KeyCode.R)){ResetRun();return;}
        if(Input.GetKeyDown(KeyCode.Return)||g=="PALM")StartRun();
        if(Input.GetKeyDown(KeyCode.P)||Input.GetKeyDown(KeyCode.Escape))
        {if(State==Phase.Driving)State=Phase.Paused;else if(State==Phase.Paused)State=Phase.Driving;}
        if(State!=Phase.Driving){braking=false;Effects.Apply(false,0,false);return;}
        if(g=="UNKNOWN") {gestureReleased+=dt;if(gestureReleased>.3f)heldSteer="UNKNOWN";}
        else
        {
            gestureReleased=0;
            if((g=="LEFT"||g=="RIGHT")&&g!=heldSteer){ChangeLane(g=="LEFT"?-1:1);heldSteer=g;}
            else if(g=="PALM"||g=="FIST")heldSteer="UNKNOWN";
        }
        if(Input.GetKeyDown(KeyCode.LeftArrow)||Input.GetKeyDown(KeyCode.A))ChangeLane(-1);
        if(Input.GetKeyDown(KeyCode.RightArrow)||Input.GetKeyDown(KeyCode.D))ChangeLane(1);
        bool brake=Input.GetKey(KeyCode.S)||Input.GetKey(KeyCode.DownArrow)||Input.GetKey(KeyCode.Space)||g=="FIST"||captureBrake;
        bool boost=Input.GetKey(KeyCode.W)||Input.GetKey(KeyCode.UpArrow)||g=="PALM";
        float speedBefore=Speed;braking=brake;
        StepSpeed(dt,brake,boost);Effects.Apply(brake,speedBefore);float advance=Speed/3.6f*dt;Distance+=advance;
        player.GetComponent<SportsCarVisual>()?.Roll(advance);
        float target=(Lane-1)*3.3f, delta=target-player.position.x;
        player.position=Vector3.Lerp(player.position,new Vector3(target,0,0),1-Mathf.Exp(-9*dt));
        player.rotation=Quaternion.Slerp(player.rotation,Quaternion.Euler(brake&&Speed>5?2.5f:0,delta*4,-delta*2),1-Mathf.Exp(-8*dt));
        foreach(var t in scenery){t.position-=Vector3.forward*advance;if(t.position.z < -40)t.position+=Vector3.forward*440;}
        spawnTimer-=dt;
        if(spawnTimer<=0 && Speed>10){SpawnTraffic();spawnTimer=Random.Range(2f,3.3f);}
        // Front-to-back order allows a follower to brake for a slower vehicle ahead.
        traffic.Sort((a,b)=>b.transform.position.z.CompareTo(a.transform.position.z));
        for(int i=0;i<traffic.Count;i++)
        {
            var car=traffic[i];float targetSpeed=car.Cruise;
            for(int j=0;j<i;j++)
            {
                var lead=traffic[j];
                if(Mathf.Abs(lead.transform.position.x-car.transform.position.x)>1)continue;
                float gap=lead.transform.position.z-car.transform.position.z-lead.HalfLength-car.HalfLength;
                targetSpeed=Mathf.Min(targetSpeed,FollowingSpeed(car.Cruise,lead.Speed,gap));
            }
            bool trafficBrake=targetSpeed<car.Speed-.3f;
            car.Speed=Mathf.MoveTowards(car.Speed,targetSpeed,(trafficBrake?9:2)*dt);
            car.Animate(dt,trafficBrake);
        }
        for(int i=traffic.Count-1;i>=0;i--)
        {
            var car=traffic[i];var t=car.transform;float oldZ=t.position.z;
            t.position+=Vector3.forward*(car.Speed-Speed/3.6f)*dt;
            if(Overlaps(player.position.x,t.position.x,oldZ,t.position.z,car.HalfWidth,car.HalfLength))Crash();
            if(t.position.z < -18-car.HalfLength || t.position.z>210){if(t.position.z < -18)passed++;Destroy(car.gameObject);traffic.RemoveAt(i);}
        }
    }
    public static float FollowingSpeed(float cruise,float leadSpeed,float gap)
    {return Mathf.Min(cruise,Mathf.Max(0,leadSpeed+(gap-12)/1.8f));}
    TrafficVehicle CreateTraffic(TrafficVehicle.Kind kind,int lane,float z)
    {
        Color[] colors={new Color(.15f,.65f,.35f),new Color(.2f,.42f,.8f),new Color(.9f,.42f,.12f),new Color(.15f,.45f,.65f)};
        var root=new GameObject(kind.ToString());var car=root.AddComponent<TrafficVehicle>();
        car.Build(kind,Mat(colors[(int)kind]),trafficVisualPrefab);
        root.transform.position=new Vector3((lane-1)*3.3f,0,z);traffic.Add(car);return car;
    }
    void SpawnTraffic()
    {
        int lane=Random.Range(0,3),nearSpawn=0;
        foreach(var car in traffic)
        {
            if(car.transform.position.z>108)nearSpawn++;
            if(Mathf.Abs(car.transform.position.x-(lane-1)*3.3f)<1 && car.transform.position.z>92)return;
        }
        if(nearSpawn>=2)return; // Avoid creating a three-wide wall at the spawn point.
        CreateTraffic((TrafficVehicle.Kind)(trafficSequence++%4),lane,140);
    }
    public void PrepareTrafficPreview()
    {
        if(System.Array.IndexOf(System.Environment.GetCommandLineArgs(),"--traffic-capture")<0)return;
        ResetRun();keyboardOnly=true;StartRun();Speed=110;spawnTimer=100;
        CreateTraffic(TrafficVehicle.Kind.ExpressBus,0,17);
        CreateTraffic(TrafficVehicle.Kind.Truck,2,26);
        CreateTraffic(TrafficVehicle.Kind.Sedan,1,43);
        CreateTraffic(TrafficVehicle.Kind.Sports,0,55);
        captureBrake=true;
    }
    void LateUpdate()
    {
        float dt=Time.deltaTime;
        chase.transform.position=Vector3.Lerp(chase.transform.position,new Vector3(player.position.x*.32f,3.7f,-7.4f),1-Mathf.Exp(-4*dt));
        chase.fieldOfView=Mathf.Lerp(chase.fieldOfView,58+Speed*.035f,1-Mathf.Exp(-3*dt));
        chase.transform.LookAt(new Vector3(player.position.x*.45f,1,16));
    }
    void OnDestroy(){foreach(var m in materials.Values)Destroy(m);if(crashSound!=null)Destroy(crashSound);}
    void Styles()
    {
        if(small!=null)return;
        small=new GUIStyle(GUI.skin.label){fontSize=16,fontStyle=FontStyle.Bold};small.normal.textColor=new Color(.78f,.88f,.90f);
        large=new GUIStyle(small){fontSize=42};large.normal.textColor=Color.white;
        title=new GUIStyle(small){fontSize=22};title.normal.textColor=new Color(.16f,.94f,.91f);
    }
    void Panel(Rect r)
    {GUI.color=new Color(.025f,.045f,.07f,.92f);GUI.DrawTexture(r,Texture2D.whiteTexture);GUI.color=new Color(.1f,.88f,.86f);GUI.DrawTexture(new Rect(r.x,r.y,3,r.height),Texture2D.whiteTexture);GUI.color=Color.white;}
    void Label(float x,float y,string text,GUIStyle style){GUI.Label(new Rect(x,y,650,65),text,style);}
    void OnGUI()
    {
        Styles();GUI.matrix=Matrix4x4.TRS(Vector3.zero,Quaternion.identity,new Vector3(Screen.width/1280f,Screen.height/720f,1));
        Panel(new Rect(28,25,290,122));Label(46,37,"DESERT SIGNAL  /  01",title);Label(46,70,Speed.ToString("000")+"  km/h",large);
        if(braking){GUI.color=new Color(1,.22f,.09f);GUI.Label(new Rect(46,149,280,30),"BRAKING / STOP LAMPS ON",small);GUI.color=Color.white;}
        Panel(new Rect(998,25,254,122));Label(1018,36,"DISTANCE / SCORE",small);Label(1018,66,Score.ToString("000000"),large);
        Panel(new Rect(28,548,362,145));Label(46,560,"GESTURE  /  "+(keyboardOnly?"KEYBOARD":receiver.Gesture),title);
        var packet=receiver.Packet;bool connected=receiver.Connected;
        Label(46,596,"CAMERA   "+(connected?packet.camera:"OFFLINE"),small);
        Label(46,623,"MODEL      "+(connected?packet.model:"OFFLINE"),small);
        Label(46,650,keyboardOnly?"K: enable gestures":"K: keyboard only  |  UDP 5055",small);
        Panel(new Rect(916,574,336,119));Label(935,589,"LANE  /  "+new[]{"LEFT","CENTER","RIGHT"}[Lane],title);
        for(int i=0;i<3;i++){GUI.color=i==Lane?new Color(.1f,.92f,.87f):new Color(.2f,.28f,.32f);GUI.DrawTexture(new Rect(936+i*96,631,85,10),Texture2D.whiteTexture);}GUI.color=Color.white;
        Label(936,653,State==Phase.Driving?"P: pause   R: reset":"LOCAL DRIVING SIMULATOR",small);
        string detail=receiver.Error??(connected?packet.detail:"Start Python bridge for hand control; keyboard is ready.");
        GUI.Label(new Rect(406,664,493,45),detail,new GUIStyle(small){fontSize=12,wordWrap=true});
        if(State!=Phase.Driving)
        {
            Panel(new Rect(355,210,570,294));Label(385,235,State==Phase.Ready?"DRIVE WITH YOUR HANDS":State==Phase.Paused?"SESSION PAUSED":"RUN COMPLETE",title);
            Label(385,282,State==Phase.Crashed?"SCORE  "+Score.ToString("000000"):"CHASE THE HORIZON",large);
            Label(385,346,"A / D : steer    W : boost    S / SPACE : brake",small);
            Label(385,376,"Hand: LEFT / RIGHT    PALM: boost    FIST: brake",small);
            if(GUI.Button(new Rect(385,431,510,46),State==Phase.Ready?"ENTER / PALM   -   START DRIVE":State==Phase.Paused?"RESUME   [P]":"TRY AGAIN   [R]"))
            {if(State==Phase.Ready)StartRun();else if(State==Phase.Paused)State=Phase.Driving;else ResetRun();}
        }
        if(crashFlash>0){GUI.color=new Color(1,.15f,.04f,crashFlash*.4f);GUI.DrawTexture(new Rect(0,0,1280,720),Texture2D.whiteTexture);GUI.color=Color.white;}
    }
}
