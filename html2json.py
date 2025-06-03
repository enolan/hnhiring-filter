# Convert HN thread HTML to JSONL

import argparse
from bs4 import BeautifulSoup
import json
from pathlib import Path


def is_top_level(tr):
    """
    Return True if the comment row is a top-level post (indent == 0).
    """
    ind_td = tr.find("td", class_="ind")
    return ind_td and ind_td.get("indent") == "0"


def extract_post(tr):
    """
    Given a <tr class="athing comtr"> element, extract id, user, timestamp, and text.
    """
    post_id = tr.get("id")
    user_tag = tr.find("a", class_="hnuser")
    age_tag = tr.find("span", class_="age")
    comment_div = tr.find("div", class_="commtext")

    return {
        "id": post_id,
        "user": user_tag.get_text(strip=True) if user_tag else None,
        "timestamp": (
            age_tag["title"] if age_tag and age_tag.has_attr("title") else None
        ),
        "text": comment_div.get_text(separator="\n", strip=True) if comment_div else "",
    }


def main():
    parser = argparse.ArgumentParser(description="Convert HN thread HTML to JSONL")
    parser.add_argument("input_path", help="Path to the input HTML file")
    parser.add_argument("output_path", help="Path to the output JSONL file")

    args = parser.parse_args()

    input_path = Path(args.input_path)
    output_path = Path(args.output_path)

    # Parse the HTML
    with input_path.open("r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    # Collect all top‑level posts
    posts = [
        extract_post(tr)
        for tr in soup.find_all("tr", class_="athing comtr")
        if is_top_level(tr)
    ]

    # Write to JSON Lines
    with output_path.open("w", encoding="utf-8") as out_file:
        for post in posts:
            json_line = json.dumps(post, ensure_ascii=False)
            out_file.write(json_line + "\n")

    print(f"Wrote {len(posts)} posts to {output_path}")


if __name__ == "__main__":
    main()
