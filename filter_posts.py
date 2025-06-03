#!/usr/bin/env python3
# Filter JSONL posts to find new posts not in the reference file

import argparse
import json
from pathlib import Path


def load_post_ids(jsonl_path):
    """
    Load all post IDs from a JSONL file into a set.
    """
    post_ids = set()
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                post = json.loads(line)
                if "id" in post and post["id"]:
                    post_ids.add(post["id"])
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse line in {jsonl_path}: {e}")
                continue
    return post_ids


def filter_new_posts(reference_ids, target_jsonl_path):
    """
    Generator that yields posts from target_jsonl_path that are not in reference_ids.
    """
    with target_jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                post = json.loads(line)
                if post["id"] not in reference_ids:
                    yield post
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse line in {target_jsonl_path}: {e}")
                continue


def main():
    parser = argparse.ArgumentParser(
        description="Filter JSONL posts to find new posts not in reference file"
    )
    parser.add_argument("reference_file", help="JSONL file containing reference posts")
    parser.add_argument("target_file", help="JSONL file to filter")
    parser.add_argument("output_file", help="Output JSONL file for new posts")

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

    # Load reference post IDs
    print(f"Loading reference post IDs from {reference_path}")
    reference_ids = load_post_ids(reference_path)
    print(f"Found {len(reference_ids)} reference posts")

    # Filter and write new posts
    print(f"Filtering posts from {target_path}")
    new_posts = list(filter_new_posts(reference_ids, target_path))

    with output_path.open("w", encoding="utf-8") as out_file:
        for post in new_posts:
            json_line = json.dumps(post, ensure_ascii=False)
            out_file.write(json_line + "\n")

    print(f"Wrote {len(new_posts)} new posts to {output_path}")
    return 0


if __name__ == "__main__":
    exit(main())
