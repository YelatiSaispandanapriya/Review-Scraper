#!/usr/bin/env python3
"""
SaaS Review Scraper - G2, Capterra, TrustRadius
Author: Assistant
Date: 2025
"""

import argparse
import json
import time
import os
import re
from datetime import datetime
from pathlib import Path

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException



# HTML parsing
from bs4 import BeautifulSoup


class ReviewScraper:
    def __init__(self, chromedriver_path):
        """Initialize scraper with ChromeDriver path"""
        self.chromedriver_path = chromedriver_path
        self.driver = None
        self.wait = None

    def setup_driver(self):
        """Setup Chrome WebDriver with options"""
        try:
            options = webdriver.ChromeOptions()
            # options.add_argument('--headless')  # Uncomment for headless mode
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument("--log-level=3")
            options.add_argument("--disable-logging")
            service = Service(self.chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 15)

            print("✅ Chrome WebDriver initialized successfully!")
            return True

        except Exception as e:
            print(f"❌ Failed to initialize WebDriver: {e}")
            return False

    def close_driver(self):
        """Close WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                print("🔒 WebDriver closed successfully!")
            except:
                pass
            self.driver = None

    def parse_date(self, date_str, source):
        """Parse date string based on source format"""
        if not date_str:
            return None

        date_str = date_str.strip()
        try:
            if source == 'g2':
                # G2 formats: 'Sep 15, 2025' or 'Sep 2025'
                if re.match(r'\w{3}\s\d{1,2},?\s\d{4}', date_str):
                    return datetime.strptime(date_str, '%b %d, %Y').date()
                elif re.match(r'\w{3}\s\d{4}', date_str):
                    return datetime.strptime(date_str, '%b %Y').date()

            elif source == 'capterra':
                # Capterra: 'September 15, 2025'
                return datetime.strptime(date_str, '%B %d, %Y').date()

            elif source == 'trustradius':
                # TrustRadius: 'Sep 15, 2025'
                return datetime.strptime(date_str, '%b %d, %Y').date()

        except ValueError:
            # Try alternative formats
            for fmt in ['%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d']:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue

        print(f"⚠️  Could not parse date: '{date_str}' for {source}")
        return None

    def search_product(self, source, company):
        """Search for company and return product reviews URL"""
        try:
            print(f"🔍 Searching for '{company}' on {source}...")

            # Base search URLs
            search_urls = {
                'g2': f"https://www.g2.com/search?query={company.replace(' ', '%20')}",
                'capterra': f"https://www.capterra.com/search?query={company.replace(' ', '%20')}",
                'trustradius': f"https://www.trustradius.com/search?query={company.replace(' ', '%20')}"
            }

            self.driver.get(search_urls[source])
            time.sleep(3)

            # Source-specific product link selectors
            selectors = {
                'g2': "a[href*='/products/'][href*='/reviews']",
                'capterra': "a[href*='/p/'][href*='/reviews/']",
                'trustradius': "a[href*='/products/'][href*='/reviews']"
            }

            link = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selectors[source])))
            product_url = link.get_attribute('href')

            print(f"✅ Found product page: {product_url}")
            return product_url

        except TimeoutException:
            raise ValueError(f"❌ Could not find '{company}' on {source}. Check company name spelling.")
        except Exception as e:
            raise Exception(f"❌ Search failed: {e}")

    def scrape_g2_reviews(self, product_url, start_date, end_date):
        """Scrape G2 reviews from a product URL using HTML parsing."""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException, NoSuchElementException
        from bs4 import BeautifulSoup
        import time

        print(f"📄 Scraping G2 reviews from {product_url}")
        self.driver.get(product_url)
        time.sleep(3)

        reviews = []
        page_count = 0

        while True:
            page_count += 1
            print(f"📑 Processing G2 page {page_count}...")

            # Wait for reviews to load
            try:
                self.wait.until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, "div.elv-flex.elv-flex-col.elv-gap-2.md\\:elv-gap-6")
                    )
                )
            except TimeoutException:
                print("⚠️ Timeout waiting for reviews to load")
                break

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            # review_elements = soup.select("div.elv-flex.elv-flex-col.elv-gap-2.md\\:elv-gap-6")

            review_elements = soup.find_all("div", attrs={"data-poison": True})
            # for div in review_elements:
            #     print(div)

            time.sleep(10)

            if not review_elements:
                print("⚠️  No review elements found on this page")
                break

            page_reviews = []

            for elem in review_elements:
                try:
                    # Reviewer info
                    reviewer_elem = elem.select_one('div[itemprop="author"] meta[itemprop="name"]')
                    reviewer = reviewer_elem.get('content', 'Anonymous') if reviewer_elem else 'Anonymous'

                    job_elem = elem.select_one('div.elv-text-xs.elv-font-regular')
                    job_title = job_elem.get_text(strip=True) if job_elem else ""

                    company_size_elem = elem.select('div.elv-text-xs.elv-font-regular')
                    company_size = company_size_elem[2].get_text(strip=True) if len(company_size_elem) > 2 else ""

                    # Date
                    date_elem = elem.select_one('meta[itemprop="datePublished"]')
                    date_str = date_elem.get('content') if date_elem else None
                    # review_date = self.parse_date(date_str, 'g2') if date_str else None
                    review_date = date_str


                    # Rating
                    rating_elem = elem.select_one('span[itemprop="reviewRating"] meta[itemprop="ratingValue"]')
                    rating = rating_elem.get('content', '') if rating_elem else ""

                    # Title
                    title_elem = elem.select_one('div[itemprop="name"]')
                    title = title_elem.get_text(strip=True) if title_elem else "No title"

                    # Review text
                    text_elem = elem.select_one('div[itemprop="reviewBody"]')
                    text = text_elem.get_text(strip=True) if text_elem else ""

                    start_date = datetime.strptime(str(start_date), "%Y-%m-%d").date()
                    end_date = datetime.strptime(str(end_date), "%Y-%m-%d").date()
                    current_date = datetime.strptime(str(date_str), "%Y-%m-%d").date()

                    # Check if current_date is within the range (inclusive)
                    if start_date <= current_date <= end_date:
                        print("✅ Date is within the given range")
                    else:
                        print("❌ Date is out of range")
                        break

                    review_data = {
                        'title': title,
                        'description': text,
                        'date': date_str,
                        'parsed_date': str(review_date) if review_date else None,
                        'rating': rating,
                        'reviewer': reviewer,
                        'job_title': job_title,
                        'company_size': company_size,
                        'source': 'g2'
                    }

                    # Only add if meaningful content
                    if title != "No title" and (text or rating):
                        page_reviews.append(review_data)
                except Exception as e:
                    print(f"⚠️  Error parsing G2 review: {e}")
                    continue

            reviews.extend(page_reviews)
            print(f"✅ Found {len(page_reviews)} reviews on this page (Total: {len(reviews)})")

            #  Pagination: click Next button
            try:
                pagination_links = self.driver.find_elements(By.CSS_SELECTOR, "ul.pagination a")

                next_button = None
                for link in pagination_links:
                    if "Next" in link.text:  # Look for text "Next ›"
                        next_button = link
                        break

                if next_button and next_button.is_displayed():
                    print("🔄 Clicking Next page...")
                    self.driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(4)  # wait for page to load
                else:
                    print("⏹️ No more pages to scrape")
                    break
            except NoSuchElementException:
                print("⏹️  Next page button not found - end of reviews")
                break

        return reviews

    def scrape_trustradius_reviews(self, product_name, start_date, end_date):
        """Search for a product on TrustRadius and scrape its reviews within a date range."""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException, NoSuchElementException
        from bs4 import BeautifulSoup
        from datetime import datetime
        import time

        def open_product_page(name):
            """Search product and open the first suggestion."""
            print(f"🔍 Searching for product: {name}")
            self.driver.get("https://www.trustradius.com/")
            search_box = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Search']"))
            )
            time.sleep(4)
            search_box.clear()
            search_box.send_keys(name)
            time.sleep(5)

            try:
                first_result = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "ul.autocomplete__list li a"))
                )
                time.sleep(2)
                product_url = first_result.get_attribute("href")
                first_result.click()
                time.sleep(4)
                print(f"✅ Opened product page: {product_url}")
                time.sleep(3)
                return product_url
            except Exception as e:
                print(f"⚠️ Could not open product: {e}")
                return None

        def parse_review(elem):
            """Extract review details from a BeautifulSoup element."""
            try:
                reviewer = elem.select_one("span.reviewCard__reviewerName")
                reviewer = reviewer.get_text(strip=True) if reviewer else "Anonymous"

                job_title = elem.select_one("span.reviewCard__reviewerRole")
                job_title = job_title.get_text(strip=True) if job_title else ""

                date_elem = elem.select_one("span.reviewCard__reviewDate")
                date_str = date_elem.get_text(strip=True) if date_elem else None
                review_date = None
                if date_str:
                    try:
                        review_date = datetime.strptime(date_str, "%B %d, %Y").date()
                    except:
                        pass

                rating_elem = elem.select_one("meta[itemprop='ratingValue']")
                rating = rating_elem.get("content") if rating_elem else ""

                title_elem = elem.select_one("h3.reviewCard__title")
                title = title_elem.get_text(strip=True) if title_elem else "No title"

                text_elem = elem.select_one("div.reviewCard__body")
                text = text_elem.get_text(strip=True) if text_elem else ""

                # Date filter
                if review_date:
                    start_date_obj = datetime.strptime(str(start_date), "%Y-%m-%d").date()
                    end_date_obj = datetime.strptime(str(end_date), "%Y-%m-%d").date()
                    if not (start_date_obj <= review_date <= end_date_obj):
                        print(f"❌ Skipping review ({date_str}) - out of range")
                        return None
                    print("✅ Date is within range")

                return {
                    "title": title,
                    "description": text,
                    "date": str(review_date) if review_date else date_str,
                    "rating": rating,
                    "reviewer": reviewer,
                    "job_title": job_title,
                    "source": "trustradius",
                }
            except Exception as e:
                print(f"⚠️ Error parsing review: {e}")
                return None

        # STEP 1: Open product page
        product_url = open_product_page(product_name)
        if not product_url:
            return []

        reviews, page_count = [], 0

        # STEP 2: Scrape reviews across pages
        while True:
            page_count += 1
            print(f"📑 Processing TrustRadius page {page_count}...")

            try:
                self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.reviewCard")))
            except TimeoutException:
                print("⚠️ Timeout waiting for reviews")
                break

            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            review_elements = soup.select("div.reviewCard")

            if not review_elements:
                print("⚠️ No reviews found on this page")
                break

            page_reviews = []
            for elem in review_elements:
                review = parse_review(elem)
                if review:
                    page_reviews.append(review)

            reviews.extend(page_reviews)
            print(f"✅ Found {len(page_reviews)} reviews (Total: {len(reviews)})")

            # STEP 3: Pagination
            try:
                next_button = self.driver.find_element(By.CSS_SELECTOR, "a[aria-label='Next Page']")
                if next_button and next_button.is_displayed():
                    print("🔄 Clicking Next page...")
                    self.driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(4)
                else:
                    print("⏹️ No more pages")
                    break
            except NoSuchElementException:
                print("⏹️ Next page button not found - end of reviews")
                break

        return reviews

    def scrape_reviews(self, source, company, start_date, end_date):
        """Main scraping method"""
        try:
            # Search for product
            product_url = self.search_product(source, company)

            # Source-specific scraping
            if source == 'g2':
                reviews = self.scrape_g2_reviews(product_url, start_date, end_date)
            elif source == 'capterra':
                reviews = self.scrape_capterra_reviews(product_url, start_date, end_date)
            elif source == 'trustradius':
                reviews = self.scrape_trustradius_reviews(product_url, start_date, end_date)
            else:
                raise ValueError(f"Unsupported source: {source}")

            print(f"\n🎉 Scraping complete! Found {len(reviews)} reviews")
            return reviews

        except Exception as e:
            print(f"❌ Scraping failed: {e}")
            return []


def validate_inputs(company, start_date, end_date):
    """Validate input parameters"""
    errors = []

    if not company or not company.strip():
        errors.append("Company name cannot be empty")

    try:
        start_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_obj = datetime.strptime(end_date, '%Y-%m-%d').date()

        if start_obj > end_obj:
            errors.append("Start date must be before or equal to end date")

        # Don't allow future dates
        today = datetime.now().date()
        if end_obj > today:
            end_obj = today
            print(f"⚠️  End date adjusted to today: {today}")

    except ValueError:
        errors.append("Dates must be in YYYY-MM-DD format")

    if errors:
        raise ValueError("\n".join(errors))

    return True


def save_reviews(reviews, company, source, output_dir="output"):
    """Save reviews to JSON file"""
    if not reviews:
        print("⚠️  No reviews to save")
        return None

    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)

    # Clean company name for filename
    safe_company = re.sub(r'[^\w\s-]', '', company).strip().replace(' ', '_')
    filename = f"{safe_company}_{source}_reviews_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(output_dir, filename)

    # Sort reviews by date (newest first)
    if reviews:
        reviews.sort(key=lambda x: x.get('parsed_date', ''), reverse=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(reviews, f, indent=2, ensure_ascii=False)

    print(f"💾 Reviews saved to: {filepath}")
    return filepath


def main():
    """Main function"""
    print("=" * 50)
    print("🚀 SaaS Review Scraper Starting...")
    print("=" * 50)

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Scrape SaaS reviews from G2, Capterra, TrustRadius')
    parser.add_argument('--company', required=True, help='Company name (e.g., "Slack")')
    parser.add_argument('--start', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--source', required=True,
                        choices=['g2', 'capterra', 'trustradius'],
                        help='Review source')
    parser.add_argument('--chromedriver', default='chromedriver.exe',
                        help='Path to ChromeDriver (default: chromedriver.exe in current directory)')

    args = parser.parse_args()

    # Validate inputs
    try:
        validate_inputs(args.company, args.start, args.end)
        print(f"📋 Parameters: Company='{args.company}', Start='{args.start}', End='{args.end}', Source='{args.source}'")
    except ValueError as e:
        print(f"❌ Input validation failed: {e}")
        return 1

    # Parse dates
    start_date = datetime.strptime(args.start, '%Y-%m-%d').date()
    end_date = datetime.strptime(args.end, '%Y-%m-%d').date()

    # Check ChromeDriver
    chromedriver_path = args.chromedriver
    if not os.path.exists(chromedriver_path):
        print(f"❌ ChromeDriver not found at: {chromedriver_path}")
        print("💡 Make sure chromedriver.exe is in the project folder")
        return 1

    print(f"🔧 Using ChromeDriver: {chromedriver_path}")

    # Initialize scraper
    scraper = ReviewScraper(chromedriver_path)

    try:
        # Setup WebDriver
        if not scraper.setup_driver():
            print("❌ Failed to setup WebDriver")
            return 1

        # Scrape reviews
        reviews = scraper.scrape_reviews(args.source, args.company, start_date, end_date)

        # Save results
        if reviews:
            filepath = save_reviews(reviews, args.company, args.source)

            print("\n📊 SUMMARY:")
            print(f"   Total Reviews: {len(reviews)}")
            print(f"   Date Range: {args.start} to {args.end}")
            print(f"   Source: {args.source.upper()}")
            print(f"   Company: {args.company}")
            print(f"   Output: {filepath}")

            # Show sample review
            if reviews:
                sample = reviews[0]
                print(f"\n📝 Sample Review:")
                print(f"   Title: {sample['title'][:50]}...")
                print(f"   Reviewer: {sample['reviewer']}")
                print(f"   Date: {sample['date']}")
                print(f"   Rating: {sample['rating']}")
        else:
            print("⚠️  No reviews found in the specified date range")
            print("💡 Try widening the date range or check company name spelling")

        return 0

    except KeyboardInterrupt:
        print("\n⏹️  Scraping interrupted by user")
        return 1

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        pass
        scraper.close_driver()


if __name__ == "__main__":
    exit(main())