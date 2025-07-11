import re
import sys
import time
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException
import json
import requests
from visualizer import visualize
from pollinations import analyze_local_image
from generateReport import generate_html_report

# ======================
# == CONFIG CONSTANTS ==
# ======================

# URL to scrape
try:
    URL = input("url:")
    url = requests.get(URL, allow_redirects=True).url
    URL = url[0:url.find("?entry=t"):] + "?hl=en"
    print(URL)

except:
    sys.exit(1)

# HEADLESS MODE
HEADLESS = True

# SELECTORS
PLACE_TITLE_XPATH = (
    "/html/body/div[1]/div[3]/div[8]/div[9]/div/div/div[1]/div[2]/div/div[1]/div/"
    "div/div[2]/div/div[1]/div[1]/h1"
)

REVIEWS_COUNT_XPATH = (
    "/html/body/div[1]/div[3]/div[8]/div[9]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/"
    "div/div[1]/div[2]/div/div[1]/div[2]/span[2]/span/span/span"
)
REVIEWS_COUNT_XPATH2 = (
    "/html/body/div[1]/div[3]/div[8]/div[9]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div/div[1]/div[2]/div/div[1]/div[2]/span[2]/span/span"
)

REVIEW_TAB_BUTTON_XPATH_2 = (  # For two tabs
    "/html/body/div[1]/div[3]/div[8]/div[9]/div/div/div[1]/div[2]/div/div[1]/div/div/div[3]/"
    "div/div/button[2]/div[2]/div[2]"
)

REVIEW_TAB_BUTTON_XPATH_3 = (
    "/html/body/div[1]/div[3]/div[8]/div[9]/div/div/div[1]/div[2]/div/div[1]/div/div/div[3]/"
    "div/div/button[3]/div[2]/div[2]"
)

# CSS class for the container holding the main tabs (Overview, Reviews, About, etc.)
CONTAINER_CLASS_RWPXGD = "RWPxGd"

# CSS class for the "Show more" button that expands truncated review text
SHOW_MORE_BUTTON_CLASS = "w8nwRe"

# CSS selector for the button that reverts translated text back to the original language
SHOW_ORIGINAL_TEXT_SELECTOR = "button.kyuRq.fontTitleSmall.WOKzJe"

# CSS class for each individual review card/container
REVIEW_CONTAINER_CLASS = "jJc9Ad"

# CSS class for the span containing the review text inside a review card
REVIEW_TEXT_CLASS = "wiI7pd"

# Possible CSS classes for the span that holds the review date (multiple variants)
DATE_CLASSES = ["rsqaWe", "xRkPPb"]

# CSS class for the element that directly shows a numeric/textual rating (e.g., "5.0")
RATING_TEXT_CLASS = "fzvQIb"

# CSS class for the container that holds the star icons for a rating
STAR_CONTAINER_CLASS = "kvMYJc"

# CSS class for each filled star icon inside the star container
FILLED_STAR_CLASS = "elGi1d"

# — Core selector classes for review vs. owner blocks — #

# CSS class for the parent div that wraps an actual user’s review text
REVIEW_BLOCK_CLASS = "MyEned"

# CSS class for the parent div that wraps the owner’s response block
OWNER_BLOCK_CLASS = "CDe7pd"

# — Selectors specific to service details inside a review — #

# CSS class for the wrapper div around both the "Services" label and the list of services
SERVICES_PARENT_CLASS = "PBK6be"

# CSS class for each span inside the services wrapper that contains a service entry
SERVICES_ENTRY_CLASS = "RfDO5c"


# ==================
# == MAIN DRIVER ==
# ==================

def initialize_driver(headless: bool = True) -> WebDriver:
    """Initialize a headless Firefox WebDriver."""
    options = Options()
    options.headless = headless
    service = Service()
    driver = webdriver.Firefox(service=service, options=options)
    return driver


def initialize_english_firefox():
    options = Options()
    options.set_preference("intl.accept_languages",
                           "en-US")  # Change "fr" to your desired language code (e.g., "en-US", "ar", etc.)

    # Initialize the WebDriver
    driver = webdriver.Firefox(options=options)

    return driver


def navigate_to_url(driver: WebDriver, url: str) -> None:
    """Navigate to the given URL and wait for initial load."""
    driver.get(url)
    time.sleep(3)  # Allow time for initial page load


def get_place_title(driver: WebDriver) -> str:
    """Extract the place title from the page."""
    try:
        title_element = driver.find_element(By.XPATH, PLACE_TITLE_XPATH)
        title = title_element.text.strip()
        return title if title else "Unknown Place"
    except Exception as e:
        print("Failed to extract place title:", e)
        return "Unknown Place"


def get_total_reviews(driver: WebDriver) -> Optional[int]:
    """Click the reviews button and extract the total number of reviews."""
    try:
        try:
            element = driver.find_element(By.XPATH, REVIEWS_COUNT_XPATH)
            element.click()
            time.sleep(2)
            text = element.text
            number = int(re.search(r"\d+", text).group())
            print(f"Found {number} reviews.")
            return number
        except:
            element = driver.find_element(By.XPATH, REVIEWS_COUNT_XPATH2)
            element.click()
            time.sleep(2)
            text = element.text
            number = int(re.search(r"\d+", text).group())
            print(f"Found {number} reviews.")
            return number
    except (NoSuchElementException, AttributeError, ValueError) as e:
        print("Failed to extract number of reviews:", e)
        return None


def click_review_tab(driver: WebDriver) -> None:
    """Click the 'Reviews' tab inside the reviews section."""
    try:
        container = driver.find_element(By.CLASS_NAME, CONTAINER_CLASS_RWPXGD)
        buttons = container.find_elements(By.TAG_NAME, "button")
        if len(buttons) == 3:

            review_button = driver.find_element(By.XPATH, REVIEW_TAB_BUTTON_XPATH_2)
        else:
            review_button = driver.find_element(By.XPATH, REVIEW_TAB_BUTTON_XPATH_3)
        review_button.click()
        time.sleep(2)
    except Exception as e:
        print("Review tab not found or already open:", e)


def scroll_to_load_reviews(driver: WebDriver, total_reviews: int) -> None:
    """Scroll the reviews section to load all content."""
    batches = max((total_reviews // 10) + 2, 5)
    last_height = 0

    for i in range(batches):
        driver.execute_script(
            """
            const pane = Array.from(document.querySelectorAll('div')).find(div => {
                const s = window.getComputedStyle(div).overflowY;
                return (s === 'auto' || s === 'scroll') && div.scrollHeight > div.clientHeight;
            });
            if (pane) {
                pane.scrollTop = pane.scrollHeight;
            }
            """
        )
        time.sleep(2)

        new_height = driver.execute_script(
            """
            const pane = Array.from(document.querySelectorAll('div')).find(div => {
                const s = window.getComputedStyle(div).overflowY;
                return (s === 'auto' || s === 'scroll') && div.scrollHeight > div.clientHeight;
            });
            return pane ? pane.scrollHeight : 0;
            """
        )

        if new_height == last_height:
            print(f"No more new reviews after {i + 1} scrolls.")
            break
        last_height = new_height

    print("Finished scrolling. All reviews should be loaded.")


def expand_show_more_buttons(driver: WebDriver) -> None:
    """Expand all 'Show more' text sections."""
    try:
        buttons = driver.find_elements(By.CLASS_NAME, SHOW_MORE_BUTTON_CLASS)
        for btn in buttons:
            try:
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(0.2)
            except Exception as e:
                print("Could not expand review:", e)
    except Exception as e:
        print("No 'Show more' buttons found:", e)

def extract_reviews_data(driver: WebDriver) -> List[Dict]:
    reviews = []
    cards = driver.find_elements(By.CLASS_NAME, REVIEW_CONTAINER_CLASS)

    for card in cards:
        try:
            # 1) USER REVIEW TEXT (only under MyEned)
            try:
                review_block = card.find_element(By.CLASS_NAME, REVIEW_BLOCK_CLASS)
                review_text = review_block.find_element(By.CLASS_NAME, REVIEW_TEXT_CLASS).text.strip()
            except:
                # no actual review → skip this card
                continue

            # 2) SERVICES (only if we have review_text)
            services = []
            try:
                svc_wrapper = card.find_element(By.CLASS_NAME, SERVICES_PARENT_CLASS)
                # skip the first <div> (the “Services” label), process any further <div> entries
                entries = svc_wrapper.find_elements(By.XPATH, "./div[position()>1]")
                for entry in entries:
                    # each entry has a span.RfDO5c containing the actual service list
                    svc = entry.find_element(By.CLASS_NAME, SERVICES_ENTRY_CLASS).text.strip()
                    if svc:
                        services.append(svc)
            except:
                pass

            if services:
                review_text += f" (Services: {'; '.join(services)})"

            # 3) DATE
            review_date = None
            for cls in DATE_CLASSES:
                try:
                    review_date = card.find_element(By.CLASS_NAME, cls).text.strip()
                    break
                except:
                    continue
            if not review_date:
                continue

            # 4) RATING
            try:
                rating = card.find_element(By.CLASS_NAME, RATING_TEXT_CLASS).text.strip()
            except:
                try:
                    stars = card.find_element(By.CLASS_NAME, STAR_CONTAINER_CLASS) \
                        .find_elements(By.CLASS_NAME, FILLED_STAR_CLASS)
                    rating = f"{len(stars)}/5"
                except:
                    rating = "N/A"

            # 5) OWNER RESPONSE
            owner_text = None
            try:
                owner_block = card.find_element(By.CLASS_NAME, OWNER_BLOCK_CLASS)
                owner_text = owner_block.find_element(By.CLASS_NAME, REVIEW_TEXT_CLASS).text.strip()
            except:
                pass

            # collect
            reviews.append({
                "date": review_date,
                "rating": rating,
                "text": review_text,
                "owner": owner_text
            })

        except Exception as e:
            print("Skipped one card due to:", e)
            continue

    return reviews


def display_reviews(reviews_data: List[Dict]) -> None:
    """Display scraped reviews in a readable format, including owner responses."""
    for idx, review in enumerate(reviews_data, start=1):
        print(f"{idx}. Date:   {review['date']}")
        print(f"   Rating: {review['rating']}")
        print(f"   Review: {review['text']}")
        if review.get('owner'):
            print(f"   Owner:  {review['owner']}")
        print("-" * 60)


# =================
# == MAIN FUNCTION ==
# =================

def main():
    driver = initialize_driver()
    try:
        navigate_to_url(driver, URL)

        # Extract and display place title
        place_title = get_place_title(driver)
        print(f"\n{'=' * 60}")
        print(f"Place: {place_title}")
        print(f"{'=' * 60}\n")

        total_reviews = get_total_reviews(driver)
        if total_reviews:
            click_review_tab(driver)
            scroll_to_load_reviews(driver, total_reviews)
            expand_show_more_buttons(driver)
            # show_original_text(driver)
            reviews_data = extract_reviews_data(driver)
            # display_reviews(reviews_data)
            driver.quit()
            save_reviews_to_file(reviews_data, place_title)

        else:
            print("No reviews found.")

    finally:
        driver.quit()




def save_reviews_to_file(reviews: List[Dict], title: str):
    """Save the list of reviews to a JSON file named after the place."""
    filename = f"{title.replace(' ', '_')}_reviews.json"
    imagepath=f"{title.replace(' ', '_')}_visual.png"
    data_str = json.dumps(reviews, ensure_ascii=False, indent=2)

    with open(filename, 'w', encoding='utf-8') as file:
        file.write(data_str)

    print(f"Saved {len(reviews)} reviews to {filename}")
    print("Creating Visualization..")
    visualize(filename, output_path=imagepath, background_color="white")
    print("Visual created...")

    print('Analyzing with AI...')
    resp = analyze_local_image(imagepath)
    print("Local Image Analysis generated...")

    print("Generating report....")
    generate_html_report(image_path=imagepath,output_html_file="report.html",markdown_text=resp['choices'][0]['message']['content'])


if __name__ == "__main__":
    main()
