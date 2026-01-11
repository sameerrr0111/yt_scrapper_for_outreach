# YouTube Channel Scraper with Airtable Integration

A **Python + Selenium scraper** to collect YouTube channel data for specific topics and automatically upload structured information to Airtable. Originally built to find content creators for outreach (e.g., video editing clients), but can be adapted for other responsible use cases.

---

## Features

- Search YouTube by **niche keywords** (finance, personal development, etc.)
- Collect hundreds of video links via controlled scrolling
- Scrape each channel’s *About* page for:
  - Subscribers, total views, total videos
  - Joining date, country / location
  - Channel description
  - External links (Instagram, Twitter, Discord, TikTok, etc.)
- Filter duplicates automatically (both from the same search and Airtable)
- Batch upload to Airtable with retry handling
- Handles **edge cases**:
  - Broken or unavailable channel pages
  - YouTube redirect links decoded to real social URLs
  - Rate-limiting avoidance via random sleep between requests

---

## Hidden / Advanced Features

- Skips channels already present in Airtable
- Avoids revisiting the same channel multiple times
- Safe handling of API failures and retries
- Structured output allows filtering by subscriber count, country, or social platform presence

---

## Create a .env file in the project root (do not commit real keys to GitHub):
```bash
AIRTABLE_API_KEY=your_airtable_api_key_here
AIRTABLE_BASE_ID=your_airtable_base_id_here
```

## Usage
#### 1. Clone the repository:
```bash
git clone https://github.com/yourusername/yt-scraper.git
cd yt-scraper
```
#### 2. Install dependencies:
```bash
pip install -r requirements.txt
```
#### 3. Run the scraper:
```bash
python yt_filter8.py
```
