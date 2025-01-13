import os
import unittest
from unittest.mock import patch, MagicMock
from app import app, get_video_list, send_video, BUCKET_NAME

class AppTestCase(unittest.TestCase):
    def setUp(self):
        # Set up the test client
        app.testing = True
        self.client = app.test_client()

    @patch('app.send_from_directory')
    def test_favicon(self, mock_send_from_directory):
        # Mock the send_from_directory response
        mock_send_from_directory.return_value = "Favicon"
        response = self.client.get('/favicon.ico')
        mock_send_from_directory.assert_called_once_with(
            os.path.join(os.getcwd(), 'static'),
            'favicon.ico', mimetype='image/vnd.microsoft.icon'
        )
        self.assertEqual(response.status_code, 200)

    @patch('app.render_template')
    @patch('app.get_video_list')
    def test_index(self, mock_get_video_list, mock_render_template):
        # Mock get_video_list and render_template
        mock_get_video_list.return_value = ["video1.mp4", "video2.mp4"]
        mock_render_template.return_value = "Rendered Template"
        response = self.client.get('/')
        mock_get_video_list.assert_called_once()
        mock_render_template.assert_called_once_with('index.html', videos=["video1.mp4", "video2.mp4"])
        self.assertEqual(response.status_code, 200)

    @patch('app.storage_client.bucket')
    def test_video(self, mock_bucket):
        # Mock bucket and blob
        mock_blob = MagicMock()
        mock_blob.open.return_value.read.side_effect = [b"chunk1", b"chunk2", b""]
        mock_bucket.return_value.blob.return_value = mock_blob

        response = self.client.get('/video/test_video.mp4')
        mock_bucket.assert_called_once_with(BUCKET_NAME)
        mock_bucket.return_value.blob.assert_called_once_with('test_video.mp4')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "video/mp4")

    @patch('app.get_video_list')
    @patch('app.send_video')
    def test_video_latest(self, mock_send_video, mock_get_video_list):
        # Mock get_video_list and send_video
        mock_blob = MagicMock()
        mock_blob.updated = 123456789
        mock_blob.name = "test_video.mp4"
        mock_get_video_list.return_value = [mock_blob]
        mock_send_video.return_value = "Video Streamed"

        response = self.client.get('/video_latest')
        mock_get_video_list.assert_called_once()
        mock_send_video.assert_called_once_with(mock_blob)
        self.assertEqual(response.status_code, 200)

    @patch('app.render_template')
    def test_latest(self, mock_render_template):
        # Mock render_template
        mock_render_template.return_value = "Rendered Template"
        response = self.client.get('/latest')
        mock_render_template.assert_called_once_with("latest.html", video_url="/video_latest")
        self.assertEqual(response.status_code, 200)

    @patch('app.storage_client.get_bucket')
    def test_get_video_list(self, mock_get_bucket):
        # Mock bucket and list_blobs
        mock_blob = MagicMock()
        mock_blob.name = "video.mp4"
        mock_get_bucket.return_value.list_blobs.return_value = [mock_blob]

        videos = get_video_list()
        mock_get_bucket.assert_called_once_with(BUCKET_NAME)
        self.assertEqual(len(videos), 1)
        self.assertEqual(videos[0].name, "video.mp4")

if __name__ == '__main__':
    unittest.main()
