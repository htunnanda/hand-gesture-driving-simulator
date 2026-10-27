using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using UnityEngine;

[Serializable]
public class GesturePacket
{
    public int v;
    public string session, gesture, camera, model, detail;
    public long seq;
    public float confidence;
}

// Non-blocking, main-thread polling: no Unity APIs on a network worker.
public sealed class GestureReceiver : MonoBehaviour
{
    public int port = 5055;
    public GesturePacket Packet { get; private set; }
    public string Error { get; private set; }
    public bool Connected => socket != null && Time.realtimeSinceStartup - received < .7f;
    public string Gesture => Connected && Packet.confidence >= .7f &&
        (Packet.camera == "ONLINE" || Packet.camera == "SIMULATED") &&
        (Packet.model == "ONLINE" || Packet.model == "SIMULATED") ? Packet.gesture : "UNKNOWN";
    UdpClient socket;
    float received = -100;

    void OnEnable()
    {
        try { socket = new UdpClient(new IPEndPoint(IPAddress.Loopback, port)); socket.Client.Blocking = false; }
        catch (Exception e) { Error = "UDP unavailable: " + e.Message; socket?.Close(); socket = null; }
    }
    void Update()
    {
        if (socket == null) return;
        // Bound work per frame even if a local process floods the port.
        for (int i = 0; i < 64 && socket.Available > 0; i++)
        {
            try
            {
                var remote = new IPEndPoint(IPAddress.Loopback, 0);
                byte[] bytes = socket.Receive(ref remote);
                if (bytes.Length > 2048) continue;
                var p = JsonUtility.FromJson<GesturePacket>(Encoding.UTF8.GetString(bytes));
                if (!Valid(p)) continue;
                if (Connected && Packet != null && Packet.session == p.session && p.seq <= Packet.seq) continue;
                Packet = p; received = Time.realtimeSinceStartup;
            }
            catch (Exception e) when (e is SocketException || e is ArgumentException) { }
        }
    }
    public static bool Valid(GesturePacket p)
    {
        return p != null && p.v == 1 && !string.IsNullOrEmpty(p.session) && p.seq >= 0 &&
            !float.IsNaN(p.confidence) && !float.IsInfinity(p.confidence) && p.confidence >= 0 && p.confidence <= 1 &&
            (p.gesture == "LEFT" || p.gesture == "RIGHT" || p.gesture == "PALM" || p.gesture == "FIST" || p.gesture == "UNKNOWN");
    }
    void OnDisable() { socket?.Close(); socket = null; }
}
