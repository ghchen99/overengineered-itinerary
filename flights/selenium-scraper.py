import time
import json
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KayakFlightScraper:
    def __init__(self, headless=True):
        """Initialize the Kayak flight scraper with Chrome driver."""
        self.setup_driver(headless)
        self.flights_data = []
    
    def setup_driver(self, headless=True):
        """Set up Chrome driver with appropriate options."""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        
        # Performance and anti-detection options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def scrape_flights(self, from_location="LHR", to_location="HKG", 
                      depart_date=None, return_date="2025-06-05"):
        """Scrape all flight data and save to JSON."""
        if not depart_date:
            depart_datetime = datetime.now() + timedelta(days=1)
            depart_date = depart_datetime.strftime("%Y-%m-%d")
        
        url = f"https://www.kayak.co.uk/flights/{from_location}-{to_location}/{depart_date}/{return_date}?sort=bestflight_a"
        
        logger.info(f"Navigating to: {url}")
        self.driver.get(url)
        
        try:
            # Handle cookies first
            logger.info("Handling cookie consent...")
            self.handle_cookies_priority()
            
            # Wait for flight results to load
            logger.info("Waiting for flight results to load...")
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='flight-card'], .nrc6, .Flights-Results-FlightResultItem"))
            )
            
            # Scroll to load more results
            self.scroll_and_load_all()
            
            # Extract all flight data
            logger.info("Extracting flight data...")
            self.extract_all_flights()
            
            # Save to JSON
            self.save_to_json(from_location, to_location, depart_date, return_date)
            
        except TimeoutException:
            logger.error("Timeout waiting for flight results to load")
            self.save_page_source_for_debugging()
        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            self.save_page_source_for_debugging()
    
    def handle_cookies_priority(self):
        """Handle cookie consent banners with priority on rejection."""
        priority_reject_selectors = [
            "//button[.//div[contains(text(), 'Reject all')]]",
            "button:contains('Reject all')",
            "button.RxNS:contains('Reject all')",
        ]
        
        secondary_reject_selectors = [
            "[data-testid='uc-reject-all-button']",
            ".Button-No-Standard-Style.Uc-Bottomsheet-Button.Uc-Bottomsheet-Button_Decline",
            "[aria-label='Reject all']",
            "button[id*='reject']",
            "button[class*='reject']",
        ]
        
        # Try priority selectors first
        for selector in priority_reject_selectors:
            try:
                if selector.startswith("//"):
                    cookie_button = WebDriverWait(self.driver, 8).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                else:
                    # Convert CSS :contains to XPath
                    if ":contains(" in selector:
                        xpath_selector = self.css_contains_to_xpath(selector)
                        cookie_button = WebDriverWait(self.driver, 8).until(
                            EC.element_to_be_clickable((By.XPATH, xpath_selector))
                        )
                    else:
                        cookie_button = WebDriverWait(self.driver, 8).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                
                self.driver.execute_script("arguments[0].scrollIntoView(true);", cookie_button)
                time.sleep(1)
                cookie_button.click()
                logger.info(f"SUCCESS: Clicked cookie rejection button")
                time.sleep(3)
                return True
                
            except TimeoutException:
                continue
            except Exception as e:
                continue
        
        # Try secondary selectors
        for selector in secondary_reject_selectors:
            try:
                cookie_button = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                cookie_button.click()
                logger.info(f"SUCCESS: Clicked secondary cookie rejection button")
                time.sleep(3)
                return True
            except:
                continue
        
        logger.warning("Could not find or click any cookie rejection buttons")
        return False
    
    def css_contains_to_xpath(self, css_selector):
        """Convert CSS :contains() pseudo-selector to XPath."""
        if ":contains(" in css_selector:
            parts = css_selector.split(":contains(")
            element_part = parts[0]
            text_part = parts[1].rstrip(")").strip("'").strip('"')
            
            if element_part == "button":
                return f"//button[contains(text(), '{text_part}')]"
            else:
                return f"//{element_part}[contains(text(), '{text_part}')]"
        return css_selector
    
    def scroll_and_load_all(self):
        """Scroll down gradually to load all available flight results."""
        logger.info("Scrolling to load all results...")
        
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        # Scroll in small steps (simulate human behavior)
        for scroll_y in range(0, last_height, 300):  # scroll every 300 pixels
            self.driver.execute_script(f"window.scrollTo(0, {scroll_y});")
            time.sleep(0.2)  # short pause to simulate gradual scrolling

    
    def extract_all_flights(self):
        """Extract data from all flight results on the page."""
        # Find all flight containers
        flight_elements = self.driver.find_elements(By.CSS_SELECTOR, ".nrc6")
        logger.info(f"Found {len(flight_elements)} flight results")
        
        for i, element in enumerate(flight_elements, 1):
            try:
                flight_data = self.extract_single_flight(element, i)
                if flight_data:
                    self.flights_data.append(flight_data)
                    logger.info(f"Extracted flight {i}: {flight_data.get('airline', 'Unknown')} - £{flight_data.get('price', 'N/A')}")
            except Exception as e:
                logger.error(f"Error extracting flight {i}: {str(e)}")
                continue
        
        logger.info(f"Successfully extracted {len(self.flights_data)} flights")
    
    def extract_single_flight(self, element, flight_num):
        """Extract data from a single flight result."""
        flight_data = {
            "flight_number": flight_num,
            "result_id": element.get_attribute("data-resultid"),
            "extraction_time": datetime.now().isoformat()
        }
        
        # Extract times
        times = self.extract_times(element)
        flight_data.update(times)
        
        # Extract price
        price = self.extract_price(element)
        flight_data["price"] = price
        
        # Extract airline
        airline = self.extract_airline(element)
        flight_data["airline"] = airline
        
        # Extract durations
        durations = self.extract_durations(element)
        flight_data.update(durations)
        
        # Extract airports
        airports = self.extract_airports(element)
        flight_data.update(airports)
        
        # Extract stops info
        stops = self.extract_stops(element)
        flight_data.update(stops)
        
        # Extract fare class
        fare_class = self.extract_fare_class(element)
        flight_data["fare_class"] = fare_class
        
        return flight_data
    
    def extract_times(self, element):
        """Extract departure and arrival times."""
        times_data = {}
        
        try:
            time_elements = element.find_elements(By.CSS_SELECTOR, ".vmXl.vmXl-mod-variant-large span")
            clean_times = []
            
            for time_elem in time_elements:
                text = time_elem.text.strip()
                if text and text != "–" and not time_elem.get_attribute("class"):
                    # Clean time format (remove +1, +2 indicators)
                    clean_time = re.sub(r'\n\+\d+', '', text)
                    if re.match(r'\d{2}:\d{2}', clean_time):
                        clean_times.append(clean_time)
            
            # Assign times based on flight legs
            if len(clean_times) >= 2:
                times_data["outbound_departure"] = clean_times[0]
                times_data["outbound_arrival"] = clean_times[1]
            if len(clean_times) >= 4:
                times_data["return_departure"] = clean_times[2]
                times_data["return_arrival"] = clean_times[3]
            
        except Exception as e:
            logger.debug(f"Error extracting times: {str(e)}")
        
        return times_data
    
    def extract_price(self, element):
        """Extract flight price."""
        try:
            price_elements = element.find_elements(By.CSS_SELECTOR, ".e2GB-price-text")
            if price_elements:
                price_text = price_elements[0].text.strip()
                # Extract numeric price
                price_match = re.search(r'£(\d+)', price_text)
                if price_match:
                    return int(price_match.group(1))
        except Exception as e:
            logger.debug(f"Error extracting price: {str(e)}")
        
        return None
    
    def extract_airline(self, element):
        """Extract airline name."""
        try:
            airline_imgs = element.find_elements(By.CSS_SELECTOR, ".c5iUd-leg-carrier img")
            if airline_imgs:
                return airline_imgs[0].get_attribute("alt")
        except Exception as e:
            logger.debug(f"Error extracting airline: {str(e)}")
        
        return None
    
    def extract_durations(self, element):
        """Extract flight durations."""
        durations_data = {}
        
        try:
            duration_elements = element.find_elements(By.CSS_SELECTOR, ".xdW8 .vmXl")
            durations = [elem.text.strip() for elem in duration_elements if elem.text.strip()]
            
            if len(durations) >= 1:
                durations_data["outbound_duration"] = durations[0]
            if len(durations) >= 2:
                durations_data["return_duration"] = durations[1]
                
        except Exception as e:
            logger.debug(f"Error extracting durations: {str(e)}")
        
        return durations_data
    
    def extract_airports(self, element):
        """Extract airport information."""
        airports_data = {}
        
        try:
            airport_elements = element.find_elements(By.CSS_SELECTOR, ".jLhY-airport-info span")
            airport_codes = []
            
            for elem in airport_elements:
                text = elem.text.strip()
                # Check if it's an airport code (3 capital letters)
                if re.match(r'^[A-Z]{3}$', text):
                    airport_codes.append(text)
            
            # Remove duplicates while preserving order
            unique_codes = []
            for code in airport_codes:
                if code not in unique_codes:
                    unique_codes.append(code)
            
            if len(unique_codes) >= 2:
                airports_data["origin"] = unique_codes[0]
                airports_data["destination"] = unique_codes[1]
                
        except Exception as e:
            logger.debug(f"Error extracting airports: {str(e)}")
        
        return airports_data
    
    def extract_stops(self, element):
        """Extract stops information."""
        stops_data = {}
        
        try:
            stops_elements = element.find_elements(By.CSS_SELECTOR, ".JWEO-stops-text")
            stops_info = []
            
            for elem in stops_elements:
                text = elem.text.strip()
                if text and text not in stops_info:
                    stops_info.append(text)
            
            if len(stops_info) >= 1:
                stops_data["outbound_stops"] = stops_info[0]
            if len(stops_info) >= 2:
                stops_data["return_stops"] = stops_info[1]
                
        except Exception as e:
            logger.debug(f"Error extracting stops: {str(e)}")
        
        return stops_data
    
    def extract_fare_class(self, element):
        """Extract fare class information."""
        try:
            # Look for fare class in price section
            price_section = element.find_element(By.CSS_SELECTOR, ".nrc6-price-section")
            price_text = price_section.text
            
            # Common fare classes
            fare_classes = ["Economy", "Economy Light", "Premium Economy", "Business", "First"]
            for fare_class in fare_classes:
                if fare_class in price_text:
                    return fare_class
                    
        except Exception as e:
            logger.debug(f"Error extracting fare class: {str(e)}")
        
        return None
    
    def save_to_json(self, from_location, to_location, depart_date, return_date):
        """Save flight data to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"./flights/results/kayak_flights_{from_location}_{to_location}_{timestamp}.json"
        
        output_data = {
            "search_parameters": {
                "origin": from_location,
                "destination": to_location,
                "departure_date": depart_date,
                "return_date": return_date,
                "search_url": self.driver.current_url,
                "extraction_time": datetime.now().isoformat(),
                "total_results": len(self.flights_data)
            },
            "flights": self.flights_data
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Successfully saved {len(self.flights_data)} flights to {filename}")
            
            # Also save a summary
            self.save_summary(filename.replace('.json', '_summary.txt'))
            
        except Exception as e:
            logger.error(f"Error saving JSON file: {str(e)}")
    
    def save_summary(self, filename):
        """Save a human-readable summary."""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"KAYAK FLIGHT SEARCH RESULTS\n")
                f.write(f"{'='*50}\n\n")
                f.write(f"Total flights found: {len(self.flights_data)}\n")
                f.write(f"Search time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                if self.flights_data:
                    prices = [f['price'] for f in self.flights_data if f.get('price')]
                    if prices:
                        f.write(f"Price range: £{min(prices)} - £{max(prices)}\n")
                        f.write(f"Average price: £{sum(prices) // len(prices)}\n\n")
                    
                    airlines = set(f['airline'] for f in self.flights_data if f.get('airline'))
                    f.write(f"Airlines found: {', '.join(sorted(airlines))}\n\n")
                
                f.write("FLIGHT DETAILS:\n")
                f.write("-" * 30 + "\n")
                
                for flight in self.flights_data:
                    f.write(f"\nFlight {flight['flight_number']}:\n")
                    f.write(f"  Airline: {flight.get('airline', 'N/A')}\n")
                    f.write(f"  Price: £{flight.get('price', 'N/A')}\n")
                    f.write(f"  Outbound: {flight.get('outbound_departure', 'N/A')} - {flight.get('outbound_arrival', 'N/A')}\n")
                    f.write(f"  Duration: {flight.get('outbound_duration', 'N/A')}\n")
                    f.write(f"  Stops: {flight.get('outbound_stops', 'N/A')}\n")
                    if flight.get('return_departure'):
                        f.write(f"  Return: {flight.get('return_departure', 'N/A')} - {flight.get('return_arrival', 'N/A')}\n")
                        f.write(f"  Return Duration: {flight.get('return_duration', 'N/A')}\n")
                    f.write(f"  Fare Class: {flight.get('fare_class', 'N/A')}\n")
            
            logger.info(f"✅ Summary saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving summary: {str(e)}")
    
    def save_page_source_for_debugging(self):
        """Save the current page source for debugging."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"kayak_debug_{timestamp}.html"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            logger.info(f"Debug page source saved to: {filename}")
        except Exception as e:
            logger.error(f"Error saving debug file: {str(e)}")
    
    def close(self):
        """Close the browser driver."""
        if hasattr(self, 'driver'):
            self.driver.quit()

def main():
    """Main function to run the scraper."""
    scraper = KayakFlightScraper(headless=False)  # Set to True for headless mode
    
    try:
        # You can customize these parameters
        scraper.scrape_flights(
            from_location="LHR",
            to_location="HKG", 
            depart_date="2025-06-01",  # Will use tomorrow if None
            return_date="2025-06-05"
        )
    finally:
        scraper.close()

if __name__ == "__main__":
    main()