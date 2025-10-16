# Review-Scraper
A Python-based automation tool that scrapes SaaS product reviews from platforms like G2 and Capterra. It uses Selenium WebDriver to collect review data (title, rating, date, reviewer info) and stores it in JSON format for analysis.

**Features**

Extracts reviews by company/product name

Supports date filtering for time-based scraping

Exports structured data to JSON

Uses ChromeDriver for automated browsing

Modular and easily customizable

**Tech Stack**

Python, Selenium, JSON

ChromeDriver, BeautifulSoup (optional)

**Setup**
git clone https://github.com/<your-username>/review-scraper.git
cd review-scraper
pip install -r requirements.txt
python scraper.py --query "Company Name" --platform g2 --output reviews.json

**Output Example**
{
  "platform": "G2",
  "company": "ExampleCorp",
  "rating": 4.5,
  "review_date": "2024-07-12",
  "title": "Great experience!",
  "review": "Easy to use and well supported."
}
