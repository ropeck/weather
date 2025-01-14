# **YouTube Video Collector API Documentation**

## **Overview**
The YouTube Video Collector API allows users to trigger the collection of a video stream from YouTube, monitor the progress, and retrieve the resulting MP4 file when the process is complete. The API supports real-time notifications using WebSocket for an efficient user experience.

---

## **Base URL**
```
http://<your-domain>/
```

---

## **Endpoints**

### 1. **Start Video Collection**
**Endpoint**:  
`POST /start_collection`

**Description**:  
Initiates the collection process for a YouTube video stream. Returns a `job_id` to track the progress.

**Request Parameters**:
- `job_id` (string): A unique identifier for the job. If not provided, the client should generate one.

**Response**:
- **Success (200)**:
  ```json
  {
    "job_id": "unique_job_id",
    "status": "started"
  }
  ```
- **Error (500)**:
  ```json
  {
    "error": "An error occurred while starting the collection."
  }
  ```

**Example Request**:
```bash
curl -X POST http://<your-domain>/start_collection \
     -d "job_id=unique_job_id"
```

---

### 2. **Check Job Status**
**Endpoint**:  
`GET /job_status/<job_id>`

**Description**:  
Fetches the current status of a specific job.

**Response**:
- **Success (200)**:
  ```json
  {
    "status": "in_progress"
  }
  ```
  or
  ```json
  {
    "status": "completed",
    "video_url": "/videos/unique_job_id.mp4"
  }
  ```
- **Error (404)**:
  ```json
  {
    "error": "Job not found"
  }
  ```

**Example Request**:
```bash
curl http://<your-domain>/job_status/unique_job_id
```

---

### 3. **Get Latest Video**
**Endpoint**:  
`GET /video_latest`

**Description**:  
Retrieves the most recently collected video.

**Response**:
- **Success (200)**: Returns a video stream in `video/mp4` format.
- **Error (404)**:
  ```json
  {
    "error": "No videos found in the bucket."
  }
  ```
- **Error (500)**:
  ```json
  {
    "error": "An error occurred while retrieving the latest video."
  }
  ```

**Example Request**:
```bash
curl http://<your-domain>/video_latest
```

---

### 4. **Serve Favicon**
**Endpoint**:  
`GET /favicon.ico`

**Description**:  
Serves the site's favicon.

**Response**:  
Returns the favicon file with a MIME type of `image/vnd.microsoft.icon`.

---

### 5. **View Latest Video Player**
**Endpoint**:  
`GET /latest`

**Description**:  
Serves an HTML page with an embedded video player for the most recent video.

**Response**:
- HTML page containing a video player.

**Example Request**:
```bash
curl http://<your-domain>/latest
```

---

## **WebSocket Events**

### **Job Update**
**Event Name**:  
`job_update`

**Description**:  
Sent by the server when the status of a job changes (e.g., from `in_progress` to `completed`).

**Payload**:
- `job_id` (string): The unique ID of the job.
- `status` (string): The updated status (`completed`).
- `video_url` (string): The URL of the resulting video.

**Example Payload**:
```json
{
  "job_id": "unique_job_id",
  "status": "completed",
  "video_url": "/videos/unique_job_id.mp4"
}
```

---

## **Examples**

### **Starting a Collection**
1. Send a `POST` request to `/start_collection` with a unique `job_id`.
2. Track the progress using WebSocket or the `/job_status/<job_id>` endpoint.
3. Once the job is complete, retrieve the video from the provided `video_url`.

### **Using WebSocket for Updates**
1. Establish a WebSocket connection to the server.
2. Listen for `job_update` events to receive real-time updates.

```javascript
const socket = io('http://<your-domain>');

// Listen for job updates
socket.on('job_update', (data) => {
    console.log(`Job ${data.job_id} is ${data.status}`);
    if (data.status === 'completed') {
        console.log(`Video URL: ${data.video_url}`);
    }
});
```

---

## **Error Handling**
- **Job Not Found**: Returned when the job ID does not exist in the system.
- **No Videos Found**: Returned when no videos are available in the bucket for `/video_latest`.

---

## **Frontend Integration**

### Embedding the Video Player
To embed the video player in your frontend:
```html
<video autoplay loop muted controls style="max-width: 100%; height: auto;">
    <source src="{{ video_url }}" type="video/mp4">
    Your browser does not support the video tag.
</video>
```

---

## **Deployment Notes**
- **Environment Variables**:
  - `BUCKET_NAME`: The name of the Google Cloud Storage bucket.
- **Dependencies**:
  - Flask
  - Flask-SocketIO
  - Google Cloud Storage
  - CacheTools
