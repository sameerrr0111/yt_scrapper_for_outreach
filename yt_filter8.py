import os  
import time
import random
import urllib.parse
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
load_dotenv()

# Airtable Setup
AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")
BASE_ID = os.environ.get("AIRTABLE_BASE_ID")
OUTPUT_TABLE = 'Finance_Channels'
url = f'https://api.airtable.com/v0/{BASE_ID}/{OUTPUT_TABLE}?fields[]=Channel%20Name'
headers = {'Authorization': f'Bearer {AIRTABLE_API_KEY}'}

scrolls = 2
TOPICS = ["personal finance","financial literacy", "money management"]
    # "how to budget", "save money tips"
    # "investing for beginners", "stock market analysis", "crypto investing", "real estate investing", "retirement planning", "build wealth", "financial freedom", "side hustle ideas", "passive income strategies", "how to make money online", "credit score tips", "debt payoff journey", "pay off debt fast", "best investing apps", "ETF vs stocks", "dividend investing", "index fund investing", "finance explained", "money habits", "net worth journey", "finance reaction video", "finance Q&A", "how to grow your savings", "budget breakdown", "finance tips for students", "YouTube finance channel",  "how to read financial statements",  "finance for beginners", "financial education videos"]

def get_scraped_channels():
    channels = set()
    offset = None

    while True:
        params = {}
        if offset:
            params['offset'] = offset
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print("Failed to fetch scraped channels:", response.text)
            break
        data = response.json()
        for record in data.get('records', []):
            name = record['fields'].get('Channel Name')
            if name:
                channels.add(name)
        offset = data.get('offset')
        if not offset:
            break
    return channels


def upload_batch_to_airtable(records):
    """Upload up to 10 records at once to Airtable"""
    url = f'https://api.airtable.com/v0/{BASE_ID}/{OUTPUT_TABLE}'
    headers = {
        'Authorization': f'Bearer {AIRTABLE_API_KEY}',
        'Content-Type': 'application/json'
    }
    # Airtable expects 'records' key with list of records having 'fields'
    data = {
        "records": [{"fields": record} for record in records]
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code not in (200, 201):
            print("Airtable batch upload error:", response.status_code, response.text)
            return False
        return True
    except Exception as e:
        print(f"❌ Exception during Airtable batch upload: {e}")
        return False

# Selenium Setup
options = Options()
# options.add_argument("--headless")  # Important
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--mute-audio")
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 15)


try:
    scraped_channels = get_scraped_channels()

    for topic_index, search_query in enumerate(TOPICS, 1):
        print(f"\n🔍 Starting Topic {topic_index}/{len(TOPICS)}: '{search_query}'")
        driver.get(f"https://www.youtube.com/results?search_query={urllib.parse.quote(search_query)}")
        time.sleep(3)

        video_links = []
        seen = set()
        scroll_pause_time = 2
        max_scrolls = scrolls

        for _ in range(max_scrolls):
            prev_count = len(video_links)
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(scroll_pause_time)

            video_elems = driver.find_elements(By.XPATH, '//a[@id="video-title"]')
            for elem in video_elems:
                href = elem.get_attribute("href")
                if href and "watch" in href and href not in seen:
                    video_links.append(href)
                    seen.add(href)

            print(f"🔄 Collected {len(video_links)} video links so far...")
            if len(video_links) == prev_count or len(video_links) >= 1000:
                print("🛑 No more new videos found. Stopping scroll.")
                break

        visited_channels = set()
        scraped_records = []

        def try_xpath(xpath):
            try:
                element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                return element.text.strip()
            except:
                return "N/A"

        for idx, video_url in enumerate(video_links, 1):
            print(f"\n[{idx}] Opening video: {video_url}")
            try:
                driver.get(video_url)
                time.sleep(4)

                channel_elem = wait.until(EC.presence_of_element_located((By.XPATH, '//ytd-channel-name//a')))
                channel_url = channel_elem.get_attribute("href")

                if channel_url in visited_channels:
                    print("⏩ Skipping already visited channel.")
                    continue
                visited_channels.add(channel_url)

                about_url = f"{channel_url}/about"
                print(f"➡️ Visiting channel About page: {about_url}")
                driver.get(about_url)
                time.sleep(4)

                if "This channel is not available" in driver.page_source or "This page isn't available" in driver.page_source:
                    print("❌ Channel page not available, skipping...")
                    continue

                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

                location = try_xpath('//*[@id="additional-info-container"]/table/tbody/tr[4]/td[2]')
                joining_date = try_xpath('//*[@id="additional-info-container"]/table/tbody/tr[5]/td[2]/yt-attributed-string/span/span')
                subscriber = try_xpath('//*[@id="additional-info-container"]/table/tbody/tr[6]/td[2]')
                videos = try_xpath('//*[@id="additional-info-container"]/table/tbody/tr[7]/td[2]')
                views = try_xpath('//*[@id="additional-info-container"]/table/tbody/tr[8]/td[2]')
                description_text = try_xpath('//*[@id="description-container"]/span')

                link_elements = driver.find_elements(By.XPATH, '//a[contains(@href, "http")]')
                links = []
                for elem in link_elements:
                    href = elem.get_attribute('href')
                    if not href:
                        continue
                    if "youtube.com/redirect" in href:
                        parsed_url = urllib.parse.urlparse(href)
                        query_params = urllib.parse.parse_qs(parsed_url.query)
                        real_url = query_params.get('q', [None])[0]
                        if real_url:
                            links.append(urllib.parse.unquote(real_url))
                    else:
                        links.append(href)

                platform_map = {
                    "tiktok.com": "TikTok",
                    "snapchat.com": "Snapchat",
                    "instagram.com": "Instagram",
                    "discord.gg": "Discord",
                    "discord.com": "Discord",
                    "twitter.com": "Twitter",
                    "youtube.com/@": "YouTube"
                }

                filtered_links = set()
                for link in links:
                    for key in platform_map:
                        if key in link:
                            filtered_links.add((platform_map[key], link))
                            break

                channel_name = channel_url.split("/")[-1] or "N/A"
                links_str = "\n".join([f"{platform}: {link}" for platform, link in sorted(filtered_links)])

                if channel_name in scraped_channels:
                    print(f"⏩ Skipping already scraped channel from Airtable: {channel_name}")
                    continue

                record = {
                    "Channel Name": channel_name,
                    "Location": location,
                    "Description": description_text,
                    "Joining Date": joining_date,
                    "Subscribers": subscriber,
                    "Videos": videos,
                    "Views": views,
                    "Links": links_str,
                    "Search": search_query
                }

                print(f"📝 Scraped data for {channel_name}: Description length {len(description_text)} chars")
                scraped_records.append(record)

            except Exception as e:
                print(f"⚠️ Error processing video {video_url}: {e}")
                continue

        # Upload to Airtable
        print(f"\nUploading {len(scraped_records)} records to Airtable in batches of 10...")
        batch_size = 10
        import json  # in case you want to save failed batches

        for i in range(0, len(scraped_records), batch_size):
            batch_records = scraped_records[i:i + batch_size]

            retries = 3
            success = False

            for attempt in range(retries):
                success = upload_batch_to_airtable(batch_records)
                if success:
                    break
                else:
                    print(f"⚠️ Retry {attempt + 1} for batch {i // batch_size + 1}")
                    time.sleep(2)  # wait before retry

            if not success:
                print(f"❌ Failed to upload batch {i // batch_size + 1} after {retries} retries")
                # Optional: save failed batch to a file
                with open("failed_batches.json", "a", encoding="utf-8") as f:
                    json.dump(batch_records, f, ensure_ascii=False)
                    f.write("\n")

            # Sleep a bit between batches to avoid rate limiting
            time.sleep(random.uniform(0.8, 1.5))

        print(f"\n✅ Done with topic '{search_query}'. Moving to next...\n{'='*60}")

finally:
    driver.quit()
    print("\n🎉 All topics scraped and uploaded.")
