import json
from groq import Groq
from config import GROQ_API_KEY
from utils.logger import get_logger

logger = get_logger(__name__)
client = Groq(api_key=GROQ_API_KEY)
MAX_CONTENT_LENGTH = 2000

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
        content = (
            r.get("raw_content")
            or r.get("content")
            or ""
        )[:MAX_CONTENT_LENGTH]
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
- For "estimated_net_worth": if multiple reputable sources report different figures,
  give a range from the lowest to the highest reported value 
  (e.g. "$970 million - $1.3 billion (estimates vary by source)"), 
  and list the specific figures with their sources in "missing_or_conflicting".
- For "career_timeline": include every distinct career milestone, role, or position 
  change mentioned across ALL sources, in chronological order, even if only one 
  source mentions it. Do not omit entries for brevity.
- For other fields, if multiple reputable public sources disagree, describe the 
  disagreement in "missing_or_conflicting" including both values and which sources 
  they came from. If no clear consensus exists and a range isn't applicable, set the 
  main field to "Conflicting public reports" instead of guessing.
- Do not invent or guess any information not present in the sources
- Note that source content may not reflect the most recent developments; if a source 
  appears dated (e.g. references old figures or past years as "current"), still report 
  what it says but do not present it as necessarily up to date.

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