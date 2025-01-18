import os
import httplib2
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, "client_secrets.json")
YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

def upload_video_to_youtube(video_path, title, description, tags, category_id):
    """
    Upload a video to YouTube and return its video ID.
    """
    flow = flow_from_clientsecrets(
        CLIENT_SECRETS_FILE,
        scope=YOUTUBE_UPLOAD_SCOPE,
        message=f"Missing {CLIENT_SECRETS_FILE}. Create one in the Google API Console.",
        redirect_uri="http://localhost:8080/"

    )

    storage = Storage(f"{os.path.basename(__file__)}-oauth2.json")
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage, argparser.parse_args([]))

    youtube = build(
        YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
        http=credentials.authorize(httplib2.Http())
    )

    tags = tags if isinstance(tags, list) else tags.split(",")

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": "public",
        },
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)

    try:
        request = youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media)
        response = None
        while response is None:
            status, response = request.next_chunk()
        if "id" in response:
            return response["id"]
        else:
            raise Exception("Unexpected response: %s" % response)
    except HttpError as e:
        raise Exception(f"An HTTP error occurred: {e.content}")
