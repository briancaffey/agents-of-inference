import pytest
import httpx
from fastapi.testclient import TestClient
from main import app  # Assuming your FastAPI app is defined in a file named main.py
from io import BytesIO

@pytest.fixture(scope="module")
def client():
    """Create a TestClient instance."""
    return TestClient(app)

@pytest.mark.asyncio
async def test_convert_img_to_vid(client):
    """Test converting an image to a video."""
    # Define the path to a sample image file
    sample_image_path = "image.png"  # Update this path to where your sample image is located

    # Open the sample image file
    with open(sample_image_path, "rb") as f:
        file_bytes_io = BytesIO(f.read())

        # Prepare the multipart/form-data payload
        payload = {
            "image_file": (file_bytes_io, f.name),
        }

        # Make a POST request to the /api/img2vid endpoint
        response = await client.post("/api/img2vid", files=payload)

        # Check if the response status code is 200 OK
        assert response.status_code == 200

        # Optionally, check the content type of the response to ensure it's a video
        assert response.headers["Content-Type"] == "video/mp4"

        # You might want to save the received video file for further inspection
        with open("received_video.mp4", "wb") as f_out:
            f_out.write(response.content)
