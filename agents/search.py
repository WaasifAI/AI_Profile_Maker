from tavily import TavilyClient
from config import TAVILY_API_KEY
from utils.logger import get_logger

logger = get_logger(__name__)

client = TavilyClient(api_key=TAVILY_API_KEY)

def search_person(name: str, context: str, max_results: int = 8):
    query = f"{name} {context}"
    logger.info(f"Searching Tavily for: {query}")

    try:
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results
        )
        results = response.get("results", [])
        logger.info(f"Tavily returned {len(results)} results")
        return results
    except Exception as e:
        logger.error(f"Tavily search failed: {e}")
        return []