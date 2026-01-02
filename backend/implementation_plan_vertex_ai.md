
# Implementation Plan: Google Cloud Vertex AI (Video Intelligence) Integration

## 1. Overview
This plan outlines the integration of **Google Cloud Video Intelligence API** to replace or augment the current local inference models. This will allow for:
1.  **"Authenticator" (Upload Analysis)**: High-accuracy, server-side verification of uploaded videos for violent content.
2.  **Live Feed Analysis**: Real-time streaming analysis of camera feeds using Google's powerful pre-trained models.

## 2. Prerequisites & Setup
Before writing code, the following GCP resources must be configured:
1.  **Google Cloud Project**: Create a new project (e.g., `violence-monitoring-ai`).
2.  **Enable APIs**:
    *   `Cloud Video Intelligence API`
    *   `Cloud Storage API` (for intermediate file storage)
3.  **Authentication**:
    *   Create a **Service Account** with roles: `Video Intelligence Editor`, `Storage Object Admin`.
    *   Download the JSON key file.
    *   Place it in `backend/keys/gcp-service-account.json`.
4.  **Cloud Storage Bucket**:
    *   Create a dedicated bucket (e.g., `vm-upload-buffer`) for temporarily staging videos before analysis.

## 3. Architecture Changes

### A. New Service Module: `CloudVideoService`
We will create `backend/app/services/cloud_video_service.py` to handle all GCP interactions. This keeps the logic separate from the local `ModelManager`.

### B. Dependency Updates
Add `google-cloud-videointelligence` and `google-cloud-storage` to `requirements.txt`.

---

## 4. Feature Implementation Strategy

### Feature 1: The "Authenticator" (Upload Analysis)
*Use Case: Verifying uploaded historical footage.*

**Workflow:**
1.  **Upload**: User uploads a video via the `Upload` page.
2.  **Staging**: The backend saves it locally, then immediately uploads it to the GCS Bucket (`vm-upload-buffer`). *Reason: The standard Video Intelligence API works best with GCS URIs.*
3.  **Request**: Call `annotate_video` with features:
    *   `LABEL_DETECTION`: To find abstract concepts ("fight", "violence", "punching").
    *   `EXPLICIT_CONTENT_DETECTION`: Specifically designed to flag adult/violent content.
4.  **Polling**: The operation is asynchronous. The backend will poll the `Operation` object until completion.
5.  **Parsing**:
    *   Check `explicit_annotation` for "Violence" likelihood (VERY_UNLIKELY to VERY_LIKELY).
    *   Check `label_annotations` for keywords like "brawl", "assault".
6.  **Cleanup**: Delete the file from GCS after analysis to save storage costs.

### Feature 2: Live Feed Analysis
*Use Case: Real-time monitoring.*

**Workflow:**
1.  **Streaming Client**: Use the `StreamingVideoIntelligenceServiceClient` (requires gRPC).
2.  **Pipeline Integration**:
    *   Modify `CameraService` to support a "Cloud Mode".
    *   Instead of capturing frames -> `ModelManager.predict()`, we implement a **Generator** function that yields video chunks (bytes) from the OpenCV stream.
3.  **Streaming Request**:
    *   Configure `StreamingVideoConfig` with `STREAMING_LABEL_DETECTION` (StationaryCamera option enabled).
    *   Open a bi-directional stream: send video chunks, receive `StreamingAnnotateVideoResponse`.
4.  **Handling Responses**:
    *   The API returns annotations live. We check for "Violence" labels with high confidence.
    *   Trigger the existing `AlertManager` (Email/SMS) if a positive hit occurs.
5.  **Optimization**:
    *   **Frame Rate**: Downsample stream to 5fps before sending to reduce bandwidth/cost.
    *   **Resolution**: Resize to 360p or 480p (Cloud AI doesn't need 4K for event detection).

---

## 5. Proposed File Structure

```text
backend/
  app/
    services/
      cloud/
        __init__.py
        gcp_config.py       # Auth & Bucket settings
        authenticator.py    # Batch processing for uploads
        live_stream.py      # gRPC streaming client
```

## 6. Cost & Latency Considerations
*   **Cost**: Video Intelligence is billed per minute. Continuous live streaming 24/7 will be expensive.
    *   *Mitigation*: Implement a "Hybrid Trigger". Use the local lightweight YOLO model to detect *people*. Only when a person is detected, switch on the Cloud Stream for violence analysis.
*   **Latency**: Cloud streaming adds 1-3 seconds of latency vs. local inference. Acceptable for monitoring but should be noted.

## 7. Next Steps
1.  Set up the GCP Project.
2.  Install `google-cloud-videointelligence`.
3.  Draft the `CloudVideoService` class skeleton.
