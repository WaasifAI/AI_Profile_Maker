from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import os
from playwright.sync_api import sync_playwright


def normalize_list_fields(profile: dict):
    list_fields = ["education", "interests", "recent_news", "career_timeline", "references", "missing_or_conflicting"]
    for field in list_fields:
        value = profile.get(field)
        if isinstance(value, str):
            profile[field] = [value]
        elif value is None:
            profile[field] = []
    return profile


def render_profile(profile: dict, image_url: str, output_path: str = "output/output_profile.html"):
    os.makedirs("output", exist_ok=True)
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("profile_template.html")

    data = dict(profile)
    data["image_url"] = image_url or "https://via.placeholder.com/130?text=No+Image"
    data["generated_date"] = datetime.now().strftime("%B %d, %Y")

    html_output = template.render(**data)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_output)

    return output_path


def html_to_png(html_path: str, png_path: str = "output/output_profile.png"):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 794, "height": 1123})
        page.goto(f"file:///{os.path.abspath(html_path)}")
        page.screenshot(path=png_path, full_page=True)
        browser.close()
    return png_path


if __name__ == "__main__":
    from agents.search import search_person
    from utils.ranking import rank_results
    from agents.profile_generator import generate_profile
    from services.image_service import get_wikipedia_image

    name = input("Enter person's name: ").strip()
    context = input("Enter context (e.g. 'CEO of Microsoft'): ").strip()

    results = search_person(name, context)
    ranked = rank_results(results, f"{name} {context} net worth biography residence")
    profile = generate_profile(name, context, ranked)

    if profile:
        profile = normalize_list_fields(profile)

        image_data = get_wikipedia_image(name)
        image_url = image_data["image_url"] if image_data else None

        html_path = render_profile(profile, image_url)
        png_path = html_to_png(html_path)
        print(f"Profile saved to: {html_path}")
        print(f"PNG saved to: {png_path}")
    else:
        print("Profile generation failed.")