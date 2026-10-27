Shader "Desert/TyreSmoke"
{
    SubShader
    {
        Tags { "Queue"="Transparent" "RenderType"="Transparent" }
        Blend SrcAlpha OneMinusSrcAlpha
        ZWrite Off Cull Off
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"
            struct appdata { float4 vertex:POSITION; fixed4 color:COLOR; float2 uv:TEXCOORD0; };
            struct v2f { float4 position:SV_POSITION; fixed4 color:COLOR; float2 uv:TEXCOORD0; };
            v2f vert(appdata v) { v2f o;o.position=UnityObjectToClipPos(v.vertex);o.color=v.color;o.uv=v.uv;return o; }
            fixed4 frag(v2f i):SV_Target
            {
                float2 p=i.uv*2-1;float r=length(p);
                float cloud=pow(saturate(1-r),1.2);
                float detail=.8+.2*sin(p.x*13+sin(p.y*8))*sin(p.y*11);
                return fixed4(i.color.rgb,i.color.a*cloud*detail);
            }
            ENDCG
        }
    }
}
