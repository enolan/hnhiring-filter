# HN Hiring Filter

I wrote this set of scripts to automate filtering through Hacker News "Who's Hiring?" threads. Job
searching is a tedious task. It sends each post to Claude with a prompt that asks if the post is a
viable candidate for me. If you want to use it yourself, you should modify the prompt in `main.py`.

## Requirements

- [Anthropic API key](https://console.anthropic.com)
- Money for API costs - it's around six tenths of a cent per post. You could cut costs by using a
  cheaper model, but it's not worth the bother. 300 posts should be less than $2.
- `uv` for package management

## Instructions

- Edit the prompt at the top of `main.py`.
- Run `uv sync` to install dependencies.
- Go to HN and download the current thread.
- Convert the HTML to JSONL: `uv run python html2json.py $PATH_TO_HTML_FILE $PATH_TO_POSTS_JSONL`
- Set the `ANTHROPIC_API_KEY` environment variable.
- If you've already run the script for this month, you can skip checking posts that you've already
  checked:
  - First time you run the script for a month:
    - Run the filtering script on every post: `uv run python main.py --output $PATH_TO_MATCHES_JSONL $PATH_TO_POSTS_JSONL`
  - Subsequent times you run the script for a month:
    - Generate a JSONL file with just the new posts: `uv run python filter_posts.py $PATH_TO_OLD_JSONL $PATH_TO_NEW_JSONL $PATH_TO_ONLY_NEW_POSTS_JSONL`
    - Run the filtering script on just the new posts: `uv run python main.py --output $PATH_TO_NEW_MATCHES_JSONL $PATH_TO_ONLY_NEW_POSTS_JSONL`
- Look at the matches. I recommend using `jq . < $PATH_TO_MATCHES_JSONL` to pretty print the JSONL
  file.

Good luck!
