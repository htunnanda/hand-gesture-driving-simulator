using System.Collections.Generic;
using UnityEngine;

// Original, brand-inspired wedge coupe. No downloaded models, logos or textures.
// Dimensions retain the game's existing collision envelope; +Z is forward.
public sealed class SportsCarVisual : MonoBehaviour
{
    readonly List<Object> owned = new List<Object>();
    readonly List<Transform> wheels = new List<Transform>();
    Material paint, carbon, glass, metal, red, led, rubber;
    public float BrakeEmission {get; private set;}

    public static void Create(Transform parent, Material bodyPaint)
    { parent.gameObject.AddComponent<SportsCarVisual>().Build(bodyPaint); }

    Material Finish(Color color, float metallic, float gloss, bool emissive=false)
    {
        var m=new Material(Resources.Load<Material>("DesertBase"));owned.Add(m);
        m.color=color;m.SetFloat("_Metallic",metallic);m.SetFloat("_Glossiness",gloss);
        if(emissive){m.EnableKeyword("_EMISSION");m.SetColor("_EmissionColor",color*2);}
        return m;
    }
    void Build(Material bodyPaint)
    {
        paint=new Material(bodyPaint);owned.Add(paint);paint.SetFloat("_Metallic",.45f);paint.SetFloat("_Glossiness",.85f);
        carbon=Finish(new Color(.018f,.022f,.026f),.25f,.4f);
        glass=Finish(new Color(.035f,.075f,.105f),.55f,.95f);
        metal=Finish(new Color(.52f,.57f,.61f),.85f,.8f);
        rubber=Finish(new Color(.016f,.018f,.021f),.0f,.22f);
        red=Finish(new Color(1,.025f,.012f),.2f,.7f,true);
        led=Finish(new Color(.76f,.94f,1),.2f,.8f,true);
        // z, half-width, lower sill, shoulder height. Rounded sections produce continuous surfaces.
        Loft("Sculpted body",new[]{
            new Vector4(-1.98f,.76f,.39f,.66f),new Vector4(-1.85f,.91f,.31f,.77f),
            new Vector4(-1.45f,.96f,.30f,.86f),new Vector4(-.95f,.94f,.30f,.87f),
            new Vector4(-.3f,.86f,.30f,.79f),new Vector4(.45f,.85f,.30f,.76f),
            new Vector4(1.15f,.94f,.31f,.73f),new Vector4(1.65f,.89f,.34f,.64f),
            new Vector4(1.99f,.72f,.40f,.51f)},paint);
        Loft("Panoramic glass",new[]{new Vector4(-1.02f,.67f,.77f,.83f),new Vector4(-.51f,.65f,.78f,1.19f),new Vector4(.25f,.61f,.75f,1.17f),new Vector4(.94f,.66f,.70f,.76f)},glass);
        Loft("Floating roof",new[]{new Vector4(-.55f,.62f,1.14f,1.22f),new Vector4(-.30f,.64f,1.16f,1.24f),new Vector4(.18f,.60f,1.14f,1.22f),new Vector4(.29f,.55f,1.12f,1.18f)},paint);
        Box("Rear diffuser",new Vector3(0,.34f,-1.89f),new Vector3(1.66f,.16f,.19f),carbon);
        Box("Front splitter",new Vector3(0,.34f,1.85f),new Vector3(1.65f,.06f,.38f),carbon);
        Box("Rear grille",new Vector3(0,.58f,-1.985f),new Vector3(1.44f,.13f,.025f),carbon);
        for(int i=-3;i<=3;i++)Box("Diffuser fin",new Vector3(i*.21f,.25f,-1.84f),new Vector3(.025f,.16f,.35f),carbon);
        for(int i=0;i<6;i++)
        {
            var vent=Box("Engine louver",new Vector3(0,.86f-i*.012f,-1.02f-i*.12f),new Vector3(.98f,.025f,.065f),carbon);
            vent.localRotation=Quaternion.Euler(-8,0,0);
        }
        foreach(int side in new[]{-1,1})
        {
            Box("Side skirt",new Vector3(side*.87f,.29f,0),new Vector3(.12f,.09f,2.4f),carbon);
            var intake=Box("Side intake",new Vector3(side*.896f,.62f,-.65f),new Vector3(.028f,.22f,.46f),carbon);
            intake.localRotation=Quaternion.Euler(0,side*-12,-side*12);
            var mirror=Sphere("Wing mirror",new Vector3(side*.91f,.94f,.43f),new Vector3(.25f,.10f,.18f),paint);
            Bar("Mirror arm",new Vector3(side*.66f,.91f,.4f),new Vector3(side*.91f,.93f,.43f),.025f,carbon);
            // Slim rear Y signatures, angled outer tips and a dark lamp recess.
            Box("Tail recess",new Vector3(side*.57f,.73f,-1.954f),new Vector3(.52f,.10f,.035f),carbon);
            Vector3 junction=new Vector3(side*.57f,.73f,-1.98f);
            Bar("Y tail lamp",new Vector3(side*.35f,.73f,-1.98f),junction,.027f,red);
            Bar("Y tail upper",junction,new Vector3(side*.79f,.78f,-1.91f),.027f,red);
            Bar("Y tail lower",junction,new Vector3(side*.79f,.69f,-1.94f),.027f,red);
            Bar("LED headlight",new Vector3(side*.45f,.62f,1.72f),new Vector3(side*.79f,.64f,1.53f),.033f,led);
            Cylinder("Exhaust surround",new Vector3(side*.51f,.37f,-2),.105f,.10f,metal,Quaternion.Euler(90,0,0));
            Cylinder("Exhaust opening",new Vector3(side*.51f,.37f,-2.055f),.074f,.008f,carbon,Quaternion.Euler(90,0,0));
            foreach(float z in new[]{-1.24f,1.21f})Wheel(side,z);
            Bar("Rear flying buttress",new Vector3(side*.64f,1.13f,-.50f),new Vector3(side*.83f,.86f,-1.3f),.065f,paint);
        }
        Box("Active rear lip",new Vector3(0,.88f,-1.81f),new Vector3(1.58f,.045f,.17f),paint);
        Box("High brake strip",new Vector3(0,.895f,-1.91f),new Vector3(.48f,.025f,.025f),red);
        SetBrake(false);
        // Small neutral badge, intentionally no manufacturer logo.
        Box("Rear badge",new Vector3(0,.72f,-1.993f),new Vector3(.12f,.025f,.01f),metal);
    }
    Transform Box(string name,Vector3 pos,Vector3 size,Material material)
    {return Primitive(PrimitiveType.Cube,name,pos,size,material);}
    Transform Sphere(string name,Vector3 pos,Vector3 size,Material material)
    {return Primitive(PrimitiveType.Sphere,name,pos,size,material);}
    Transform Primitive(PrimitiveType type,string name,Vector3 pos,Vector3 size,Material material)
    {
        var g=GameObject.CreatePrimitive(type);g.name=name;g.transform.SetParent(transform,false);
        g.transform.localPosition=pos;g.transform.localScale=size;g.GetComponent<Renderer>().sharedMaterial=material;Destroy(g.GetComponent<Collider>());return g.transform;
    }
    Transform Cylinder(string name,Vector3 pos,float radius,float depth,Material material,Quaternion rotation)
    {var t=Primitive(PrimitiveType.Cylinder,name,pos,new Vector3(radius*2,depth*.5f,radius*2),material);t.localRotation=rotation;return t;}
    void Bar(string name,Vector3 a,Vector3 b,float width,Material material)
    {var t=Box(name,(a+b)*.5f,new Vector3(width,width,Vector3.Distance(a,b)),material);t.localRotation=Quaternion.LookRotation(b-a);}
    void Wheel(int side,float z)
    {
        var pivot=new GameObject("Wheel assembly").transform;pivot.SetParent(transform,false);pivot.localPosition=new Vector3(side*.91f,.36f,z);wheels.Add(pivot);
        var tire=Cylinder("Performance tire",pivot.localPosition,.355f,.22f,rubber,Quaternion.Euler(0,0,90));tire.SetParent(pivot,true);
        var rim=Cylinder("Alloy rim",new Vector3(side*1.03f,.36f,z),.26f,.022f,carbon,Quaternion.Euler(0,0,90));rim.SetParent(pivot,true);
        for(int i=0;i<5;i++)
        {
            float a=i*Mathf.PI*2/5;
            Vector3 start=new Vector3(side*1.047f,.36f,z),end=start+new Vector3(0,Mathf.Cos(a),Mathf.Sin(a))*.235f;
            int before=transform.childCount;Bar("Forged spoke",start,end,.035f,metal);transform.GetChild(before).SetParent(pivot,true);
        }
        var hub=Cylinder("Hub",new Vector3(side*1.053f,.36f,z),.055f,.02f,metal,Quaternion.Euler(0,0,90));hub.SetParent(pivot,true);
    }
    void Loft(string name,Vector4[] sections,Material material)
    {
        const int count=24;var vertices=new List<Vector3>();var indices=new List<int>();
        for(int s=0;s<sections.Length;s++)
        {
            var p=sections[s];
            for(int i=0;i<count;i++)
            {
                float a=i*Mathf.PI*2/count,c=Mathf.Cos(a),sn=Mathf.Sin(a);
                // Rounded rectangle, with a broad top and softly rolled shoulders.
                float x=Mathf.Sign(c)*Mathf.Pow(Mathf.Abs(c),.48f)*p.y;
                float y=(p.z+p.w)*.5f+Mathf.Sign(sn)*Mathf.Pow(Mathf.Abs(sn),.55f)*(p.w-p.z)*.5f;
                vertices.Add(new Vector3(x,y,p.x));
            }
        }
        for(int s=0;s<sections.Length-1;s++)for(int i=0;i<count;i++)
        {int a=s*count+i,b=s*count+(i+1)%count,c=a+count,d=b+count;indices.AddRange(new[]{a,b,c,b,d,c});}
        for(int end=0;end<2;end++)
        {
            int ring=end==0?0:(sections.Length-1)*count;var sec=sections[end==0?0:sections.Length-1];int center=vertices.Count;vertices.Add(new Vector3(0,(sec.z+sec.w)*.5f,sec.x));
            for(int i=0;i<count;i++){int a=ring+i,b=ring+(i+1)%count;indices.AddRange(end==0?new[]{center,b,a}:new[]{center,a,b});}
        }
        var mesh=new Mesh{name=name};owned.Add(mesh);mesh.SetVertices(vertices);mesh.SetTriangles(indices,0);mesh.RecalculateNormals();mesh.RecalculateBounds();
        var g=new GameObject(name,typeof(MeshFilter),typeof(MeshRenderer));g.transform.SetParent(transform,false);g.GetComponent<MeshFilter>().sharedMesh=mesh;g.GetComponent<Renderer>().sharedMaterial=material;
    }
    public void SetBrake(bool braking)
    { BrakeEmission=braking?4f:.25f;red.SetColor("_EmissionColor",new Color(1,.025f,.012f)*BrakeEmission);red.color=braking?new Color(1,.06f,.025f):new Color(.36f,.008f,.004f); }
    public void Roll(float metres){foreach(var wheel in wheels)wheel.Rotate(Vector3.right,metres/.355f*Mathf.Rad2Deg,Space.Self);}
    void OnDestroy(){foreach(var item in owned)Destroy(item);}
}
