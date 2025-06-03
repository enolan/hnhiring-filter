from textwrap import dedent
import argparse
import json
import sys
import os
from anthropic import Anthropic
from tqdm import tqdm

prompt = dedent("""
I'm looking for a job. Below, I'll give you a json object representing a post from the latest Hacker
news hiring thread. Read the post and respond with whether it meets the following criteria:
* The role should be primarily ML engineering. Designing, implementing, training and/or finetuning
  models, gathering data, evaluating models, that sort of thing. Use your best judgement when
  reading the post. Do not include any "developer relations" roles. The following titles are likely
  to be what I'm looking for, but the exact title is not important:
   * ML Engineer
   * Research Engineer
   * Software Engineer, ML
   * Member of Technical Staff
   * AI Engineer
* Location should be either NYC or remote and compatible with NYC working hours.
Err toward including posts when it's ambiguous. Respond with either "MATCHES" or "DOES NOT MATCH".
Include no other text in your response. Here's the job post:
{post_json}
""").strip()

def process_post(client, post):
    post_json = json.dumps(post)
    
    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=2048,
        system="You are a helpful assistant.",
        messages=[
            {"role": "user", "content": prompt.format(post_json=post_json)}
        ],
        thinking={"type": "enabled", "budget_tokens": 1024}
    )
    
    # Access the final answer (non-thinking content)
    print("Blocks:")
    for block in response.content:
        print(block)
    print(f"Usage: {response.usage.model_dump_json()}")
    final_block = response.content[-1]
    assert final_block.type == "text"
    response = final_block.text
    #print(f"Post {post['id']}: {response}")
    return response

def main():
    parser = argparse.ArgumentParser(description="Filter HN hiring posts using Claude")
    parser.add_argument("jsonl_file", help="Path to the JSONL file containing HN job posts")
    parser.add_argument("--output", "-o", help="Path to output file for matching posts", default="matching_posts.jsonl")
    parser.add_argument(
        "--workers", "-w", type=int, default=4, help="Number of parallel workers"
    )
    args = parser.parse_args()
    
    if not os.path.exists(args.jsonl_file):
        print(f"Error: File {args.jsonl_file} not found", file=sys.stderr)
        sys.exit(1)
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
        
    client = Anthropic(api_key=api_key)
    matches = 0
    processed = 0

    # Load all posts from the file
    posts = []
    with open(args.jsonl_file, "r") as f:
        for line in f:
            try:
                post = json.loads(line.strip())
                posts.append(post)
            except json.JSONDecodeError:
                print(f"Error: Invalid JSON line: {line[:50]}...", file=sys.stderr)

    total_posts = len(posts)
    print(f"Loaded {total_posts} posts. Processing with {args.workers} workers...")

    with open(args.output, "w") as outfile:
        # Process posts in parallel
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=args.workers
        ) as executor:
            # Submit all tasks
            future_to_post = {
                executor.submit(process_post, client, post): post for post in posts
            }

            # Process results as they complete
            for future in tqdm(
                concurrent.futures.as_completed(future_to_post),
                total=total_posts,
                desc="Processing posts",
                unit="post",
            ):
                try:
                    post, response = future.result()
                    processed += 1

                    if "MATCHES" in response:
                        matches += 1
                        # Print more details for matching posts
                        print(f"\nMatching Post {post.get('id', 'Unknown')}:")
                        print(f"User: {post.get('user', 'Unknown')}")
                        print(f"Text: {post.get('text', '')[:200]}...\n")

                        # Write matching post to output file
                        json.dump(post, outfile)
                        outfile.write("\n")
                        # Flush to ensure the match is written immediately
                        outfile.flush()
                except Exception as e:
                    print(f"Error processing post: {e}", file=sys.stderr)

    print(f"\nSummary: Found {matches} matching posts out of {processed} processed")
    print(f"Matching posts saved to {args.output}")

if __name__ == "__main__":
    main()