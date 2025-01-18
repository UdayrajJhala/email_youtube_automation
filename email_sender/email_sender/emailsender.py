import csv
import cv2
import os
import base64
from io import BytesIO
from PIL import Image
from django.http import JsonResponse
from django.core.mail import EmailMessage
from django.conf import settings
from .upload_video import upload_video_to_youtube

def extract_thumbnail(video_path):
    """
    Extract thumbnail from MP4 file using OpenCV.
    Returns a base64 encoded string of the thumbnail image.
    """
    try:
        # Open the video file
        video = cv2.VideoCapture(video_path)
        
        # Read the first frame
        success, frame = video.read()
        if not success:
            raise Exception("Could not read video file")
            
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image
        pil_image = Image.fromarray(frame_rgb)
        
        # Resize if needed (optional)
        max_size = (800, 450)  # 16:9 aspect ratio
        pil_image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save to BytesIO object as JPEG
        buffer = BytesIO()
        pil_image.save(buffer, format='JPEG', quality=85)
        buffer.seek(0)
        
        # Encode to base64
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        # Clean up
        video.release()
        
        return image_base64
        
    except Exception as e:
        raise Exception(f"Error extracting thumbnail: {str(e)}")

from email.mime.image import MIMEImage

def send_email_with_video(request):
    """
    Send emails with a video thumbnail linking to a YouTube video.
    """
    # Path to the CSV file
    csv_file_path = os.path.join(os.path.dirname(__file__), "emails.csv")

    # Path to your video file
    video_file_path = os.path.join(os.path.dirname(__file__), "samplevid.mp4")
    title = "Sample Video Title"
    description = "Description of the video."
    tags = ["sample", "video", "youtube"]
    category_id = "22"

    try:
        # Extract thumbnail from video file
        thumbnail_base64 = extract_thumbnail(video_file_path)
        
        # Upload the video to YouTube and get the video ID
        video_id = upload_video_to_youtube(video_file_path, title, description, tags, category_id)

        # Construct the video URL
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        ad_text = "This is an ad text. Check out this video!"

        # Read the CSV file and send emails
        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip the header row

            for row in reader:
                if len(row) < 2:
                    continue

                recipient_name = row[0].strip()
                recipient_email = row[1].strip()

                if not recipient_name or not recipient_email:
                    continue

                subject = "Check Out This Video"
                message = f"""
                    <html>
                    <body>
                        <p>Hey {recipient_name},</p>
                        <p>{ad_text}</p>
                        <p>Click the video below to watch:</p>
                        <a href="{video_url}">
                            <img src="cid:thumbnail" alt="Watch Video" 
                                 style="width: 100%; max-width: 600px;"/>
                        </a>
                    </body>
                    </html>
                """

                email = EmailMessage(
                    subject,
                    message,
                    settings.EMAIL_HOST_USER,
                    [recipient_email],
                )
                email.content_subtype = "html"

                # Create MIMEImage object for the thumbnail
                image_data = base64.b64decode(thumbnail_base64)
                image = MIMEImage(image_data, _subtype="jpeg")
                image.add_header('Content-ID', '<thumbnail>')
                image.add_header('Content-Disposition', 'inline; filename="thumbnail.jpg"')

                # Attach the image to the email
                email.attach(image)

                # Send the email
                email.send()

        return JsonResponse({"status": "Emails sent successfully!"})

    except Exception as e:
        return JsonResponse({"error": str(e)})
