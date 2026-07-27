from unittest.mock import Mock, patch

from rest_framework import status
from rest_framework.test import APITestCase

from common.factories import make_user
from instagram import views
from instagram.services import InstagramAPIError, InstagramService


class InstagramServiceTest(APITestCase):
    @patch("instagram.services.requests.request")
    def test_get_media_calls_correct_endpoint(self, mock_request):
        mock_request.return_value = Mock(status_code=200, json=lambda: {"data": [{"id": "1"}]})
        result = InstagramService().get_media("777")
        self.assertEqual(result, {"data": [{"id": "1"}]})
        kwargs = mock_request.call_args.kwargs
        self.assertEqual(kwargs["method"], "GET")
        self.assertTrue(kwargs["url"].endswith("/777/media"))
        self.assertEqual(kwargs["params"], {"fields": "id,caption"})

    @patch("instagram.services.requests.request")
    def test_get_comments_calls_correct_endpoint(self, mock_request):
        mock_request.return_value = Mock(status_code=200, json=lambda: {"data": []})
        InstagramService().get_comments("media9")
        kwargs = mock_request.call_args.kwargs
        self.assertTrue(kwargs["url"].endswith("/media9/comments"))

    @patch("instagram.services.requests.request")
    def test_reply_posts_message(self, mock_request):
        mock_request.return_value = Mock(status_code=200, json=lambda: {"id": "reply1"})
        InstagramService().reply_to_comment("c1", "Rahmat!")
        kwargs = mock_request.call_args.kwargs
        self.assertEqual(kwargs["method"], "POST")
        self.assertTrue(kwargs["url"].endswith("/c1/replies"))
        self.assertEqual(kwargs["json"], {"message": "Rahmat!"})

    @patch("instagram.services.requests.request")
    def test_non_200_raises_api_error(self, mock_request):
        mock_request.return_value = Mock(status_code=400, text="Bad token")
        with self.assertRaises(InstagramAPIError):
            InstagramService().get_media("777")


class InstagramViewsTest(APITestCase):
    def setUp(self):
        self.client.force_authenticate(make_user(username="ig_user"))

    def test_media_requires_authentication(self):
        self.client.force_authenticate(None)
        response = self.client.get("/instagram/media/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_media_returns_service_data(self):
        with patch.object(views.instagram_service, "get_media", return_value={"data": [{"id": "m1"}]}):
            response = self.client.get("/instagram/media/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"][0]["id"], "m1")

    def test_media_api_error_returns_400(self):
        with patch.object(views.instagram_service, "get_media", side_effect=InstagramAPIError("xato")):
            response = self.client.get("/instagram/media/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_comments_requires_media_id(self):
        response = self.client.get("/instagram/comments/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_comments_passes_media_id_to_service(self):
        with patch.object(views.instagram_service, "get_comments", return_value={"data": []}) as mock_get:
            response = self.client.get("/instagram/comments/", {"media_id": "m42"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_get.assert_called_once_with("m42")

    def test_reply_validates_payload(self):
        response = self.client.post("/instagram/reply/", {"comment_id": "c1"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reply_sends_message(self):
        with patch.object(views.instagram_service, "reply_to_comment", return_value={"id": "r1"}) as mock_reply:
            response = self.client.post("/instagram/reply/", {"comment_id": "c1", "message": "Salom"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_reply.assert_called_once_with("c1", "Salom")

    def test_reply_api_error_returns_400(self):
        with patch.object(views.instagram_service, "reply_to_comment", side_effect=InstagramAPIError("xato")):
            response = self.client.post("/instagram/reply/", {"comment_id": "c1", "message": "Salom"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
