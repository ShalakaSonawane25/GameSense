using System;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

namespace GameSense
{
    /// <summary>
    /// Attach this MonoBehaviour to a persistent GameObject (e.g. GameManager)
    /// in your Unity scene to automatically record and dispatch telemetry to GameSense Backend.
    /// </summary>
    public class GameSenseTelemetryClient : MonoBehaviour
    {
        [Header("Backend Configuration")]
        [Tooltip("Base URL of your FastAPI backend")]
        public string backendUrl = "http://127.0.0.1:8000/api";

        [Header("Session Metadata")]
        public string currentLevelName = "Level_1";
        public string personaType = "HUMAN"; // Set to BEGINNER, EXPLORER, SPEEDRUNNER, or AGGRESSIVE for AI bots
        public string gameVersion = "1.0.0";

        [Header("Sampling Settings")]
        [Tooltip("Seconds between position recordings")]
        public float sampleInterval = 0.5f;

        [Tooltip("Seconds between network flushes of position batches")]
        public float batchFlushInterval = 3.0f;

        // Active session state
        private string sessionId;
        private float sessionStartTime;
        private bool isSessionActive = false;

        // Local buffer for high-frequency position points
        private List<PositionSampleData> positionBuffer = new List<PositionSampleData>();
        private float lastSampleTime = 0f;
        private float lastFlushTime = 0f;

        // Session metrics accumulator
        private int totalScore = 0;
        private int totalDeaths = 0;
        private int itemsCollected = 0;
        private int enemiesDefeated = 0;

        void Awake()
        {
            DontDestroyOnLoad(gameObject);
        }

        void Start()
        {
            // Optionally auto-start session on scene load
            StartSession();
        }

        void Update()
        {
            if (!isSessionActive) return;

            // Sample player coordinates at regular intervals
            if (Time.time - lastSampleTime >= sampleInterval)
            {
                RecordCurrentPosition();
                lastSampleTime = Time.time;
            }

            // Flush buffered coordinates to backend
            if (Time.time - lastFlushTime >= batchFlushInterval && positionBuffer.Count > 0)
            {
                FlushPositions();
                lastFlushTime = Time.time;
            }
        }

        /// <summary>
        /// Registers a new playtest session with the backend.
        /// </summary>
        public void StartSession()
        {
            sessionId = "unity_" + Guid.NewGuid().ToString("N").Substring(0, 12);
            sessionStartTime = Time.time;
            isSessionActive = true;
            positionBuffer.Clear();

            string jsonPayload = $"{{\"session_id\":\"{sessionId}\",\"persona_type\":\"{personaType}\",\"level_name\":\"{currentLevelName}\",\"game_version\":\"{gameVersion}\"}}";
            StartCoroutine(PostJson($"{backendUrl}/telemetry/session/start", jsonPayload));
            Debug.Log($"[GameSense] Started Session: {sessionId} ({personaType})");
        }

        /// <summary>
        /// Records an instantaneous gameplay event (Death, Checkpoint, Item, Kill).
        /// </summary>
        public void LogEvent(string eventType, string causeOrSource = null, float customX = 0, float customY = 0)
        {
            if (!isSessionActive) return;

            float elapsed = Time.time - sessionStartTime;
            Vector3 pos = transform.position;

            if (eventType.ToUpper() == "DEATH") totalDeaths++;
            if (eventType.ToUpper().Contains("ITEM")) itemsCollected++;
            if (eventType.ToUpper().Contains("ENEMY")) enemiesDefeated++;

            string causeJson = string.IsNullOrEmpty(causeOrSource) ? "null" : $"\"{causeOrSource}\"";
            string jsonPayload = $"{{\"session_id\":\"{sessionId}\",\"event_type\":\"{eventType}\",\"level_name\":\"{currentLevelName}\",\"timestamp\":{elapsed:F2},\"x\":{pos.x:F2},\"y\":{pos.y:F2},\"z\":{pos.z:F2},\"cause_or_source\":{causeJson}}}";
            
            StartCoroutine(PostJson($"{backendUrl}/telemetry/events", jsonPayload));
        }

        /// <summary>
        /// Closes the session and sends final metrics.
        /// </summary>
        public void EndSession(bool playerWon)
        {
            if (!isSessionActive) return;

            // Final flush of any pending positions
            if (positionBuffer.Count > 0)
            {
                FlushPositions();
            }

            float duration = Time.time - sessionStartTime;
            string status = playerWon ? "COMPLETED" : "FAILED";
            isSessionActive = false;

            string jsonPayload = $"{{\"session_id\":\"{sessionId}\",\"status\":\"{status}\",\"duration_seconds\":{duration:F2},\"total_score\":{totalScore},\"total_deaths\":{totalDeaths},\"items_collected\":{itemsCollected},\"enemies_defeated\":{enemiesDefeated}}}";
            StartCoroutine(PostJson($"{backendUrl}/telemetry/session/end", jsonPayload));
            Debug.Log($"[GameSense] Ended Session {sessionId} with status: {status}");
        }

        private void RecordCurrentPosition()
        {
            Vector3 pos = transform.position;
            positionBuffer.Add(new PositionSampleData
            {
                timestamp = (float)Math.Round(Time.time - sessionStartTime, 2),
                x = (float)Math.Round(pos.x, 2),
                y = (float)Math.Round(pos.y, 2),
                z = (float)Math.Round(pos.z, 2),
                health = 100 // Bind to player's current health component
            });
        }

        private void FlushPositions()
        {
            List<PositionSampleData> toSend = new List<PositionSampleData>(positionBuffer);
            positionBuffer.Clear();

            StringBuilder sb = new StringBuilder();
            sb.Append($"{{\"session_id\":\"{sessionId}\",\"level_name\":\"{currentLevelName}\",\"positions\":[");
            for (int i = 0; i < toSend.Count; i++)
            {
                sb.Append($"{{\"timestamp\":{toSend[i].timestamp},\"x\":{toSend[i].x},\"y\":{toSend[i].y},\"z\":{toSend[i].z},\"health\":{toSend[i].health}}}");
                if (i < toSend.Count - 1) sb.Append(",");
            }
            sb.Append("]}");

            StartCoroutine(PostJson($"{backendUrl}/telemetry/positions/batch", sb.ToString()));
        }

        private IEnumerator PostJson(string url, string jsonBody)
        {
            using (UnityWebRequest req = new UnityWebRequest(url, "POST"))
            {
                byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonBody);
                req.uploadHandler = new UploadHandlerRaw(bodyRaw);
                req.downloadHandler = new DownloadHandlerBuffer();
                req.SetRequestHeader("Content-Type", "application/json");

                yield return req.SendWebRequest();

                if (req.result != UnityWebRequest.Result.Success)
                {
                    Debug.LogWarning($"[GameSense Error] POST to {url} failed: {req.error}");
                }
            }
        }

        [Serializable]
        private struct PositionSampleData
        {
            public float timestamp;
            public float x;
            public float y;
            public float z;
            public int health;
        }
    }
}
