from tavily import TavilyClient
from config import TAVILY_API_KEY
from utils.logger import get_logger

logger = get_logger(__name__)

client = TavilyClient(api_key=TAVILY_API_KEY)

def search_person(name: str, context: str, max_results: int = 8):
    query = (
    f"{name} {context} "
    "biography education career nationality "
    "current city current country net worth recent news"
).strip()
    logger.info(f"Searching Tavily for: {query}")

    try:
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_raw_content=True
        )
        results = response.get("results", [])
        logger.info(f"Tavily returned {len(results)} results")
        return results
    except Exception:
        logger.exception("Tavily search failed")
        return []