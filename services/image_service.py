import requests
from utils.logger import get_logger

logger = get_logger(__name__)

HEADERS = {
    "User-Agent": "AI-Profile-Builder/1.0 (educational project; contact: student@example.com)"
}

def get_wikipedia_image(name: str):
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{name.replace(' ', '_')}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            logger.warning(f"Wikipedia summary not found for {name} (status {response.status_code})")
            return None

        data = response.json()
        thumbnail = data.get("thumbnail", {}).get("source")

        if thumbnail:
            logger.info(f"Found Wikipedia image for {name}")
            return {
                "image_url": thumbnail,
                "source": data.get("content_urls", {}).get("desktop", {}).get("page", url)
            }
        else:
            logger.info(f"No thumbnail available for {name}")
            return None

    except Exception:
        logger.exception("Wikipedia image fetch failed")
        return None