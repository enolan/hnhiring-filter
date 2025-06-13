#!/usr/bin/env python3
# Filter JSONL posts to find new posts not in the reference file and posts with changed bodies

import argparse
import json
from pathlib import Path


def load_posts(jsonl_path):
    """
    Load all posts from a JSONL file into a dictionary indexed by post ID.
    """
    posts = {}
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                post = json.loads(line)
                if "id" in post and post["id"]:
                    posts[post["id"]] = post
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse line in {jsonl_path}: {e}")
                continue
    return posts


def filter_new_and_changed_posts(
    reference_posts, target_jsonl_path, modified_only=False
):
    """
    Generator that yields posts from target_jsonl_path that are either:
    1. Not in reference_posts (new posts) - unless modified_only is True
    2. In reference_posts but with different text content (changed posts)
    """

    with target_jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                post = json.loads(line)
                post_id = post["id"]

                if post_id not in reference_posts:
                    # New post - only yield if not in modified_only mode
                    if not modified_only:
                        yield post
                else:
                    # Check if text content has changed
                    reference_post = reference_posts[post_id]
                    target_text = post.get("text", "")
                    reference_text = reference_post.get("text", "")

                    if target_text != reference_text:
                        # Text content has changed
                        yield post
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse line in {target_jsonl_path}: {e}")
                continue


def main():
    parser = argparse.ArgumentParser(
        description="Filter JSONL posts to find new posts and posts with changed text content"
    )
    parser.add_argument("reference_file", help="JSONL file containing reference posts")
    parser.add_argument("target_file", help="JSONL file to filter")
    parser.add_argument(
        "output_file", help="Output JSONL file for new and changed posts"
    )
    parser.add_argument(
        "--modified-only",
        action="store_true",
        help="Only output posts that exist in both files but have changed text content (exclude new posts)",
    )

    args = parser.parse_args()

    reference_path = Path(args.reference_file)
    target_path = Path(args.target_file)
    output_path = Path(args.output_file)

    if not reference_path.exists():
        print(f"Error: Reference file {reference_path} does not exist")
        return 1

    if not target_path.exists():
        print(f"Error: Target file {target_path} does not exist")
        return 1

    # Load reference posts
    print(f"Loading reference posts from {reference_path}")
    reference_posts = load_posts(reference_path)
    print(f"Found {len(reference_posts)} reference posts")

    # Filter and write new and changed posts
    filter_description = (
        "modified posts only" if args.modified_only else "new and changed posts"
    )
    print(f"Filtering {filter_description} from {target_path}")
    filtered_posts = list(
        filter_new_and_changed_posts(reference_posts, target_path, args.modified_only)
    )

    with output_path.open("w", encoding="utf-8") as out_file:
        for post in filtered_posts:
            json_line = json.dumps(post, ensure_ascii=False)
            out_file.write(json_line + "\n")

    output_description = (
        "modified posts" if args.modified_only else "new and changed posts"
    )
    print(f"Wrote {len(filtered_posts)} {output_description} to {output_path}")
    return 0


if __name__ == "__main__":
    exit(main())
