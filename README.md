# Crawling financial reports
This is one of the tasks I completed as a research assistant. There are 847,963 financial reports crawled from EDGAR.

## Web Scraping Techniques
- Utilized `requests` and `BeautifulSoup` to fetch and parse webpage content.
- Employed Selenium to handle dynamic elements in the Chrome browser.

## Data Processing and Formatting
- Standardized file names by removing invalid characters (e.g., `/` and `,`) for easier storage.
- Extracted company names and CIKs from file content using regular expressions.

## Data Storage
- Created distinct file names based on report types (10-Q or 10-Q/A) and saved them in `.txt` or `.htm` formats.

## Error Handling and Retry Mechanism
- Implemented a retry mechanism (`max_retries`) with defined wait times to handle page loading issues.
- Logged failed downloads when HTTP requests returned non-200 responses.

**Pagination Handling:**
- Automatically processed multiple pages when search results exceeded 100 entries, ensuring all data was retrieved.
