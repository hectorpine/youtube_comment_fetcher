import os
import requests
import logging
from dotenv import load_dotenv
import re
import csv
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)

class YouTubeCommentsTool:
    name: str = "YouTube Comments Fetcher"
    description: str = "Fetches all comments from a specified YouTube video using the YouTube Data API."

    def _run(self, video_id: str) -> list:
        try:
            # Get API Key
            api_key = os.getenv("YOUTUBE_API_KEY")
            if not api_key:
                logging.error("YOUTUBE_API_KEY environment variable not set.")
                return []

            logging.info(f"Using API Key: {api_key}")

            comments = []
            next_page_token = None
            total_comments = self.get_current_comment_count()  # Get current comment count

            while True:
                # API request to fetch comments
                url = "https://www.googleapis.com/youtube/v3/commentThreads"
                params = {
                    "part": "snippet",
                    "videoId": video_id,
                    "pageToken": next_page_token,
                    "maxResults": 100,
                    "textFormat": "plainText",
                    "key": api_key
                }
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                # Process comments
                for item in data["items"]:
                    comment = item["snippet"]["topLevelComment"]["snippet"]
                    comments.append({
                        "author": comment["authorDisplayName"],
                        "text": comment["textDisplay"],
                        "published_at": comment["publishedAt"]
                    })

                # Periodically save comments
                if len(comments) >= 100:
                    total_comments = self.save_comments(comments, total_comments, video_id)
                    comments = []

                # Get next page token
                next_page_token = data.get("nextPageToken")
                if not next_page_token:
                    break

            # Save remaining comments
            self.save_comments(comments, total_comments, video_id)
            logging.info(f"Total {total_comments} comments fetched.")
            return comments

        except requests.exceptions.RequestException as e:
            logging.error(f"An HTTP error occurred: {e}")
            return []
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return []

    def save_comments(self, comments, start_index, video_id):
        try:
            date_str = datetime.now().strftime("%Y%m%d")
            markdown_file = f"comments_{video_id}_{date_str}.md"
            csv_file = f"comments_{video_id}_{date_str}.csv"
            json_file = f"comments_{video_id}_{date_str}.json"

            # Save to Markdown
            with open(markdown_file, "a", encoding="utf-8") as f_md:
                for i, comment in enumerate(comments, start=start_index + 1):
                    f_md.write(f"{i}. **{comment['author']}**: {comment['text']} (Published at: {comment['published_at']})\n")

            # Save to CSV
            with open(csv_file, "a", newline='', encoding="utf-8") as f_csv:
                writer = csv.writer(f_csv)
                if start_index == 0:  # Write header only once
                    writer.writerow(["Index", "Author", "Comment", "Published At"])
                for i, comment in enumerate(comments, start=start_index + 1):
                    writer.writerow([i, comment['author'], comment['text'], comment['published_at']])

            # Save to JSON
            with open(json_file, "a", encoding="utf-8") as f_json:
                json_data = {"comments": comments}
                json.dump(json_data, f_json, ensure_ascii=False, indent=4)

            return start_index + len(comments)
        except Exception as e:
            logging.error(f"Comments could not be saved: {e}")
            return start_index

    def get_current_comment_count(self):
        try:
            markdown_file = f"comments_{video_id}_{date_str}.md"
            if os.path.exists(markdown_file):
                with open(markdown_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                return len(lines)
            return 0
        except Exception as e:
            logging.error(f"Current comment count could not be retrieved: {e}")
            return 0

def extract_video_id(url):
    # This regex will match the video ID from any YouTube URL (normal, shortened, embedded)
    try:
        match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
        return match.group(1) if match else None
    except Exception as e:
        logging.error(f"Error extracting video ID: {e}")
        return None

def run():
    load_dotenv()
    video_url = input("🚀 Enter YouTube URL: ")
    video_id = extract_video_id(video_url)
    if not video_id:
        print("🚨 Invalid YouTube URL provided.")
        return

    comments_tool = YouTubeCommentsTool()
    result = comments_tool._run(video_id)
    print("Analysis Result:")
    print(result)

if __name__ == "__main__":
    run()
