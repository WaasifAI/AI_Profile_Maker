import json
from groq import Groq
from config import GROQ_API_KEY
from utils.logger import get_logger

logger = get_logger(__name__)
client = Groq(api_key=GROQ_API_KEY)

PROFILE_SCHEMA = """
{
  "executive_summary": "string",
  "full_name": "string",
  "nationality": "string",
  "current_role": "string",
  "industry": "string",
  "current_city": "string",
  "current_country": "string",
  "biography": "string",
  "career_timeline": [{"year": "string", "event": "string"}],
  "education": ["string"],
  "interests": ["string"],
  "estimated_net_worth": "string",
  "recent_news": ["string"],
  "references": [{"title": "string", "url": "string"}],
  "missing_or_conflicting": ["string"]
}
"""

def generate_profile(name: str, context: str, ranked_results: list):
    sources_text = ""
    for r in ranked_results:
        content = r.get("content", "")[:2000] # Limit content to 20,000 characters
        sources_text += (
            f"\nSource: {r.get('url', 'N/A')}"
            f"\nTitle: {r.get('title', 'N/A')}"
            f"\nContent: {content}\n"
        )

    prompt = f"""Using ONLY the source content below,
build a structured profile for: {name} ({context}).

Return ONLY valid JSON matching this exact schema.
Do not wrap the JSON in markdown.
Do not include explanations.
Do not include comments.
Do not include code fences.

Schema:
{PROFILE_SCHEMA}

Rules:
- If a field is not found in the sources, write "Not found in public sources".
- Include all sources actually used in the "references" field, with their title and url.
- If multiple reputable public sources disagree on a fact (e.g. different net worth figures),
  describe the disagreement in "missing_or_conflicting" including both values and which sources
  they came from. If no clear consensus exists, set the main field itself to
  "Conflicting public reports" instead of guessing or picking a winner.
- Do not invent or guess any information not present in the sources.

SOURCES:
{sources_text}
"""

    logger.info(f"Generating profile for {name} using Groq")
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a factual information extraction assistant. Never fabricate information."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2
        )
        raw_output = response.choices[0].message.content.strip() # Get the raw output from the LLM response

        if raw_output.startswith("```json"):
            raw_output = raw_output[7:] # Remove the opening ```json
        elif raw_output.startswith("```"):
            raw_output = raw_output[3:]
        if raw_output.endswith("```"):
            raw_output = raw_output[:-3] # Remove the closing ```
        raw_output = raw_output.strip() 

        profile = json.loads(raw_output)
        logger.info("Profile generated and parsed successfully")
        return profile

    except json.JSONDecodeError:
        logger.exception("Failed to parse LLM output as JSON")
        return None
    except Exception:
        logger.exception("Groq generation failed")
        return None