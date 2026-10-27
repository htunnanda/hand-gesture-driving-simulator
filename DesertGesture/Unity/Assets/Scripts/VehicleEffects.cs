using UnityEngine;

public sealed class VehicleEffects : MonoBehaviour
{
    ParticleSystem[] smoke = new ParticleSystem[2];
    Light[] lamps = new Light[2];
    SportsCarVisual visual;
    Material smokeMaterial;
    public bool BrakeLit { get; private set; }
    public bool Smoking { get; private set; }
    public int LiveParticles => smoke[0].particleCount + smoke[1].particleCount;
    public static bool ShouldSmoke(bool brake,float speed) => brake && speed > 35;

    void Awake()
    {
        visual=GetComponent<SportsCarVisual>();
        smokeMaterial=new Material(Resources.Load<Shader>("TyreSmoke"));
        for(int i=0;i<2;i++)
        {
            float side=i==0?-1:1;
            var lightObject=new GameObject("Brake light glow");lightObject.transform.SetParent(transform,false);
            lightObject.transform.localPosition=new Vector3(side*.58f,.65f,-2.04f);
            var light=lightObject.AddComponent<Light>();light.type=LightType.Point;light.color=new Color(1,.025f,.008f);light.range=2.4f;light.intensity=0;lamps[i]=light;
            var obj=new GameObject("Rear tyre smoke");obj.transform.SetParent(transform,false);obj.transform.localPosition=new Vector3(side*.91f,.13f,-1.3f);
            var ps=obj.AddComponent<ParticleSystem>();ps.Stop(true,ParticleSystemStopBehavior.StopEmittingAndClear);
            var main=ps.main;main.playOnAwake=false;main.loop=true;main.simulationSpace=ParticleSystemSimulationSpace.World;
            main.startLifetime=new ParticleSystem.MinMaxCurve(.6f,1.1f);main.startSpeed=.3f;main.startSize=new ParticleSystem.MinMaxCurve(.65f,.95f);main.maxParticles=100;
            main.startColor=new Color(.72f,.71f,.69f,.7f);main.startRotation=new ParticleSystem.MinMaxCurve(0,Mathf.PI*2);
            var shape=ps.shape;shape.shapeType=ParticleSystemShapeType.Sphere;shape.radius=.11f;
            var emission=ps.emission;emission.rateOverTime=0;
            var size=ps.sizeOverLifetime;size.enabled=true;size.size=new ParticleSystem.MinMaxCurve(1,new AnimationCurve(new Keyframe(0,.6f),new Keyframe(1,3.5f)));
            var color=ps.colorOverLifetime;color.enabled=true;var gradient=new Gradient();
            gradient.SetKeys(new[]{new GradientColorKey(Color.white,0),new GradientColorKey(Color.white,1)},new[]{new GradientAlphaKey(0,0),new GradientAlphaKey(1,.02f),new GradientAlphaKey(0,1)});color.color=gradient;
            var velocity=ps.velocityOverLifetime;velocity.enabled=true;velocity.space=ParticleSystemSimulationSpace.World;
            velocity.x=new ParticleSystem.MinMaxCurve(side*.6f);velocity.y=new ParticleSystem.MinMaxCurve(.8f);velocity.z=new ParticleSystem.MinMaxCurve(-3);
            var renderer=ps.GetComponent<ParticleSystemRenderer>();renderer.sharedMaterial=smokeMaterial;renderer.renderMode=ParticleSystemRenderMode.Billboard;
            renderer.shadowCastingMode=UnityEngine.Rendering.ShadowCastingMode.Off;renderer.receiveShadows=false;
            smoke[i]=ps;
        }
    }
    public void Apply(bool brake,float speed,bool active=true)
    {
        BrakeLit=active&&brake;Smoking=active&&ShouldSmoke(brake,speed);
        visual?.SetBrake(BrakeLit);
        for(int i=0;i<2;i++)
        {
            lamps[i].intensity=BrakeLit?2.5f:0;
            var emission=smoke[i].emission;emission.rateOverTime=Smoking?Mathf.Lerp(28,65,Mathf.InverseLerp(35,145,speed)):0;
            var velocity=smoke[i].velocityOverLifetime;velocity.z=new ParticleSystem.MinMaxCurve(-Mathf.Max(2,speed/3.6f*.65f));
            if(Smoking&&!smoke[i].isPlaying)smoke[i].Play();
            if(!active)smoke[i].Stop(true,ParticleSystemStopBehavior.StopEmittingAndClear);
        }
    }
    void OnDestroy(){Destroy(smokeMaterial);}
}
