using System.Collections.Generic;
using UnityEngine;

public sealed class TrafficVehicle : MonoBehaviour
{
    public enum Kind { Sports, Sedan, Truck, ExpressBus }
    public Kind Type {get;private set;}
    public float HalfLength {get;private set;}
    public float HalfWidth {get;private set;}
    public float Cruise {get;private set;}
    public float Speed;
    readonly List<Object> owned=new List<Object>();
    readonly List<Transform> wheels=new List<Transform>();
    Material paint,glass,rubber,trim,white,red;
    SportsCarVisual sport;
    float wheelRadius;
    public static Vector2 Dimensions(Kind kind)
    {return kind==Kind.Truck?new Vector2(1.13f,4):kind==Kind.ExpressBus?new Vector2(1.16f,5.1f):kind==Kind.Sedan?new Vector2(1.02f,2.3f):new Vector2(1.03f,2.05f);}
    public void Build(Kind kind,Material bodyPaint,GameObject prefab=null)
    {
        Type=kind;var dimensions=Dimensions(kind);HalfWidth=dimensions.x;HalfLength=dimensions.y;
        Cruise=kind==Kind.Truck?14:kind==Kind.ExpressBus?18:kind==Kind.Sedan?21:25;Speed=Cruise;
        if(prefab!=null){Instantiate(prefab,transform);return;}
        if(kind==Kind.Sports){SportsCarVisual.Create(transform,bodyPaint);sport=GetComponent<SportsCarVisual>();return;}
        paint=Material(bodyPaint.color,.35f);glass=Material(new Color(.035f,.085f,.12f),.6f);
        rubber=Material(new Color(.025f,.027f,.03f),0);trim=Material(new Color(.32f,.37f,.41f),.8f);
        white=Material(new Color(.88f,.90f,.89f),.2f);red=Material(new Color(.55f,.01f,.015f),.2f);red.EnableKeyword("_EMISSION");
        if(kind==Kind.Truck)Truck();else if(kind==Kind.ExpressBus)Bus();else Sedan();
        foreach(int side in new[]{-1,1})
        {
            Box("Rear lamp",new Vector3(side*(HalfWidth-.22f),kind==Kind.Sedan?.65f:.85f,-HalfLength-.015f),new Vector3(.23f,.15f,.04f),red);
            Box("Headlight",new Vector3(side*(HalfWidth-.25f),.7f,HalfLength+.015f),new Vector3(.28f,.13f,.04f),white);
        }
    }
    Material Material(Color c,float metallic)
    {var m=new Material(Resources.Load<Material>("DesertBase"));m.color=c;m.SetFloat("_Metallic",metallic);m.SetFloat("_Glossiness",.6f);owned.Add(m);return m;}
    Transform Box(string name,Vector3 p,Vector3 s,Material m)
    {return Primitive(PrimitiveType.Cube,name,p,s,m);}
    Transform Primitive(PrimitiveType type,string name,Vector3 p,Vector3 s,Material m)
    {var g=GameObject.CreatePrimitive(type);g.name=name;g.transform.SetParent(transform,false);g.transform.localPosition=p;g.transform.localScale=s;g.GetComponent<Renderer>().sharedMaterial=m;Destroy(g.GetComponent<Collider>());return g.transform;}
    void Shell(string name,Vector3 p,Vector3 size,Material m)
    {
        // Rounded rectangular cross sections and chamfered end caps.
        const int n=24;var vertices=new List<Vector3>();var tris=new List<int>();
        for(int r=0;r<4;r++)for(int i=0;i<n;i++)
        {
            float a=i*Mathf.PI*2/n,c=Mathf.Cos(a),s=Mathf.Sin(a),scale=r==0||r==3?.9f:1;
            float z=(r==0?-.5f:r==1?-.46f:r==2?.46f:.5f)*size.z;
            vertices.Add(p+new Vector3(Mathf.Sign(c)*Mathf.Pow(Mathf.Abs(c),.3f)*size.x*.5f*scale,Mathf.Sign(s)*Mathf.Pow(Mathf.Abs(s),.3f)*size.y*.5f*scale,z));
        }
        for(int r=0;r<3;r++)for(int i=0;i<n;i++){int a=r*n+i,b=r*n+(i+1)%n;tris.AddRange(new[]{a,b,a+n,b,b+n,a+n});}
        for(int end=0;end<2;end++){int center=vertices.Count;vertices.Add(p+Vector3.forward*(end==0?-.5f:.5f)*size.z);int ring=end==0?0:3*n;for(int i=0;i<n;i++){int a=ring+i,b=ring+(i+1)%n;tris.AddRange(end==0?new[]{center,b,a}:new[]{center,a,b});}}
        var mesh=new Mesh{name=name};mesh.SetVertices(vertices);mesh.SetTriangles(tris,0);mesh.RecalculateNormals();mesh.RecalculateBounds();owned.Add(mesh);
        var g=new GameObject(name,typeof(MeshFilter),typeof(MeshRenderer));g.transform.SetParent(transform,false);g.GetComponent<MeshFilter>().sharedMesh=mesh;g.GetComponent<Renderer>().sharedMaterial=m;
    }
    void Axle(float z,float radius)
    {
        wheelRadius=radius;
        foreach(int side in new[]{-1,1})
        {
            var pivot=new GameObject("Rolling wheel").transform;pivot.SetParent(transform,false);pivot.localPosition=new Vector3(side*(HalfWidth-.07f),radius,z);wheels.Add(pivot);
            var tyre=Primitive(PrimitiveType.Cylinder,"Tyre",pivot.localPosition,new Vector3(radius*2,.12f,radius*2),rubber);tyre.localRotation=Quaternion.Euler(0,0,90);tyre.SetParent(pivot,true);
            var rim=Primitive(PrimitiveType.Cylinder,"Alloy",new Vector3(side*(HalfWidth+.06f),radius,z),new Vector3(radius*1.35f,.015f,radius*1.35f),trim);rim.localRotation=Quaternion.Euler(0,0,90);rim.SetParent(pivot,true);
            for(int k=0;k<5;k++){float a=k*Mathf.PI*2/5;var bolt=Box("Wheel spoke",new Vector3(side*(HalfWidth+.08f),radius+Mathf.Cos(a)*radius*.3f,z+Mathf.Sin(a)*radius*.3f),new Vector3(.02f,.05f,radius*.55f),rubber);bolt.localRotation=Quaternion.Euler(-k*72,0,0);bolt.SetParent(pivot,true);}
        }
    }
    void Sedan()
    {
        Shell("Sedan body",new Vector3(0,.65f,0),new Vector3(1.97f,.65f,4.6f),paint);
        Shell("Sedan windows",new Vector3(0,1.13f,-.12f),new Vector3(1.62f,.62f,2.45f),glass);
        Shell("Sedan roof",new Vector3(0,1.45f,-.18f),new Vector3(1.52f,.08f,1.75f),paint);
        foreach(int side in new[]{-1,1}){Box("Door pillar",new Vector3(side*.82f,1.16f,-.12f),new Vector3(.04f,.56f,.10f),paint);Box("Door handle",new Vector3(side*.99f,.86f,-.3f),new Vector3(.03f,.035f,.18f),trim);}
        Box("Rear bumper",new Vector3(0,.43f,-2.29f),new Vector3(1.7f,.11f,.06f),trim);Axle(-1.43f,.36f);Axle(1.4f,.36f);
    }
    void Truck()
    {
        Box("Chassis",new Vector3(0,.58f,0),new Vector3(1.8f,.25f,7.8f),rubber);
        Shell("Cab",new Vector3(0,1.55f,2.65f),new Vector3(2.16f,2.05f,2.7f),paint);
        Box("Windshield",new Vector3(0,2.03f,4.005f),new Vector3(1.85f,.78f,.025f),glass);
        Box("Cab grille",new Vector3(0,1.03f,4.02f),new Vector3(1.3f,.35f,.035f),rubber);
        Shell("Cargo box",new Vector3(0,2.05f,-1.36f),new Vector3(2.22f,2.65f,5.25f),white);
        Box("Cargo rear doors",new Vector3(0,2.02f,-4.005f),new Vector3(2.02f,2.35f,.03f),trim);
        for(int side=-1;side<=1;side+=2)
        {
            Box("Cab side glass",new Vector3(side*1.085f,2.06f,2.88f),new Vector3(.025f,.75f,1.45f),glass);
            Box("Cargo stripe",new Vector3(side*1.12f,1.65f,-1.36f),new Vector3(.025f,.24f,4.9f),paint);
            Box("Door locking bar",new Vector3(side*.55f,2,-4.04f),new Vector3(.04f,2.15f,.04f),white);
            Box("Mirror",new Vector3(side*1.18f,2,3.65f),new Vector3(.15f,.32f,.14f),rubber);
        }
        Axle(2.65f,.5f);Axle(-2.3f,.5f);Axle(-3.35f,.5f);
    }
    void Bus()
    {
        Shell("Express coach body",new Vector3(0,1.83f,0),new Vector3(2.28f,2.75f,10.2f),white);
        Shell("Coach roof",new Vector3(0,3.2f,0),new Vector3(2.12f,.14f,9.65f),paint);
        Box("Panoramic windshield",new Vector3(0,2.23f,5.095f),new Vector3(1.98f,1.45f,.035f),glass);
        Box("Rear glass",new Vector3(0,2.43f,-5.095f),new Vector3(1.93f,.9f,.035f),glass);
        for(int side=-1;side<=1;side+=2)
        {
            for(int i=0;i<8;i++)Box("Passenger window",new Vector3(side*1.142f,2.38f,-3.95f+i*1.08f),new Vector3(.035f,1.05f,.96f),glass);
            Box("Express livery",new Vector3(side*1.15f,1.37f,0),new Vector3(.035f,.36f,9.7f),paint);
            for(int i=0;i<5;i++)Box("Luggage door seam",new Vector3(side*1.153f,.85f,-3.6f+i*1.65f),new Vector3(.02f,.48f,.025f),trim);
        }
        Box("Rear livery",new Vector3(0,1.37f,-5.11f),new Vector3(2,.36f,.025f),paint);
        for(int i=0;i<5;i++)Box("Engine vent",new Vector3(0,.92f+i*.07f,-5.12f),new Vector3(1.25f,.027f,.025f),rubber);
        Axle(3.3f,.48f);Axle(-3.0f,.48f);Axle(-4.05f,.48f);
    }
    public void Animate(float dt,bool braking)
    {
        sport?.Roll(Speed*dt);sport?.SetBrake(braking);
        if(red!=null)red.SetColor("_EmissionColor",new Color(1,.015f,.005f)*(braking?3:.2f));
        foreach(var wheel in wheels)wheel.Rotate(Vector3.right,Speed*dt/wheelRadius*Mathf.Rad2Deg,Space.Self);
    }
    void OnDestroy(){foreach(var item in owned)Destroy(item);}
}
