import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import re

def init_driver():
    """Undetected ChromeDriver - auto-detect Chrome version"""
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # Don't specify version - let it auto-detect
    driver = uc.Chrome(options=options, use_subprocess=True)
    return driver

def scrape_with_selenium(url):
    """Main scraper with TIMEOUT"""
    driver = None
    try:
        print(f"🤖 Starting UNDETECTED Chrome for: {url}")
        driver = init_driver()
        
        # Set page load timeout
        driver.set_page_load_timeout(30)  # Max 30 seconds
        
        print(f"🌐 Loading page...")
        try:
            driver.get(url)
        except:
            # Timeout or error - continue anyway
            print("⚠️ Page load timed out, continuing...")
        
        # Shorter wait
        time.sleep(4)  # Reduced from 6
        
        print(f"📄 Page loaded. Title: {driver.title[:50]}...")
        
        # Route to site-specific scraper
        if 'aliexpress' in url.lower():
            result = scrape_aliexpress(driver, url)
        elif 'walmart' in url.lower():
            result = scrape_walmart(driver, url)
        elif 'bestbuy' in url.lower():
            result = scrape_bestbuy(driver, url)
        elif 'newegg' in url.lower():
            result = scrape_newegg(driver, url)
        else:
            result = scrape_generic(driver, url)
        
        driver.quit()
        return result
        
    except Exception as e:
        if driver:
            try:
                driver.quit()
            except:
                pass
        
        import traceback
        print(f"❌ CRASH: {traceback.format_exc()}")
        
        return {
            'title': None,
            'price': None,
            'success': False,
            'error': f'Scraper timeout or crash. Site may be too slow or blocking.'
        }

def scrape_walmart(driver, url):
    """Walmart scraper"""
    try:
        print("🔍 Scraping Walmart...")
        
        # Save debug
        with open('walmart_debug.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("📄 Saved walmart_debug.html")
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # TITLE
        title = None
        
        # Try h1 with itemprop
        title_elem = soup.find('h1', {'itemprop': 'name'})
        if not title_elem:
            title_elem = soup.find('h1', class_=re.compile('prod.*title', re.I))
        if not title_elem:
            title_elem = soup.find('h1')
        
        if title_elem:
            title = title_elem.get_text().strip()
            print(f"✅ Title: {title[:50]}...")
        
        # Fallback to meta
        if not title:
            meta = soup.find('meta', {'property': 'og:title'})
            if meta:
                title = meta.get('content', '').strip()
        
        if not title:
            title = driver.title.split('|')[0].split('-')[0].strip()
        
        # PRICE
        price = None
        
        # Try itemprop price
        price_elem = soup.find('span', {'itemprop': 'price'})
        if not price_elem:
            # Try aria-label with price
            price_elems = soup.find_all(attrs={'aria-label': re.compile('price', re.I)})
            for elem in price_elems:
                price = extract_price(elem.get_text())
                if price:
                    break
        else:
            price = extract_price(price_elem.get_text())
        
        # Fallback: search for price patterns
        if not price:
            price_patterns = re.findall(r'\$\s*([\d,]+\.?\d{2})', driver.page_source)
            for match in price_patterns:
                potential_price = extract_price(match)
                if potential_price and 0.99 <= potential_price <= 50000:
                    price = potential_price
                    break
        
        # Try Selenium directly
        if not price:
            try:
                price_elem = driver.find_element(By.CSS_SELECTOR, '[itemprop="price"]')
                price = extract_price(price_elem.text or price_elem.get_attribute('content'))
            except:
                pass
        
        print(f"💰 Price: ${price if price else 'NOT FOUND'}")
        
        if title and price:
            return {
                'title': title[:250],
                'price': price,
                'success': True,
                'error': None
            }
        else:
            return {
                'title': title,
                'price': price,
                'success': False,
                'error': f'Walmart: title={bool(title)}, price={bool(price)}. Check walmart_debug.html'
            }
            
    except Exception as e:
        return {
            'title': None,
            'price': None,
            'success': False,
            'error': f'Walmart error: {str(e)}'
        }


def scrape_bestbuy(driver, url):
    """BestBuy scraper"""
    try:
        print("🔍 Scraping BestBuy...")
        
        # Save debug
        with open('bestbuy_debug.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("📄 Saved bestbuy_debug.html")
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # TITLE
        title = None
        
        # BestBuy uses specific classes
        title_elem = soup.find('h1', class_=re.compile('heading', re.I))
        if not title_elem:
            title_elem = soup.find('h1')
        
        if title_elem:
            title = title_elem.get_text().strip()
            print(f"✅ Title: {title[:50]}...")
        
        # Meta fallback
        if not title:
            meta = soup.find('meta', {'property': 'og:title'})
            if meta:
                title = meta.get('content', '').strip()
        
        if not title:
            title = driver.title.split('|')[0].split('-')[0].strip()
        
        # PRICE
        price = None
        
        # BestBuy typically uses aria-hidden spans for prices
        price_elems = soup.find_all('span', {'aria-hidden': 'true'})
        for elem in price_elems:
            text = elem.get_text().strip()
            if '$' in text:
                price = extract_price(text)
                if price and 0.99 <= price <= 50000:
                    break
        
        # Try priceView class
        if not price:
            price_elem = soup.find('div', class_=re.compile('priceView', re.I))
            if price_elem:
                price = extract_price(price_elem.get_text())
        
        # Try data-price attribute
        if not price:
            price_elem = soup.find(attrs={'data-price': True})
            if price_elem:
                price = extract_price(price_elem.get('data-price', ''))
        
        # Selenium fallback
        if not price:
            try:
                price_elem = driver.find_element(By.CSS_SELECTOR, '[class*="priceView"]')
                price = extract_price(price_elem.text)
            except:
                pass
        
        # Last resort: regex
        if not price:
            price_patterns = re.findall(r'\$\s*([\d,]+\.?\d{2})', driver.page_source)
            for match in price_patterns:
                potential_price = extract_price(match)
                if potential_price and 9.99 <= potential_price <= 50000:
                    price = potential_price
                    break
        
        print(f"💰 Price: ${price if price else 'NOT FOUND'}")
        
        if title and price:
            return {
                'title': title[:250],
                'price': price,
                'success': True,
                'error': None
            }
        else:
            return {
                'title': title,
                'price': price,
                'success': False,
                'error': f'BestBuy: title={bool(title)}, price={bool(price)}. Check bestbuy_debug.html'
            }
            
    except Exception as e:
        return {
            'title': None,
            'price': None,
            'success': False,
            'error': f'BestBuy error: {str(e)}'
        }


def scrape_newegg(driver, url):
    """Newegg scraper"""
    try:
        print("🔍 Scraping Newegg...")
        
        # Save debug
        with open('newegg_debug.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("📄 Saved newegg_debug.html")
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # TITLE
        title = None
        
        # Newegg uses page-title class
        title_elem = soup.find('h1', class_='product-title')
        if not title_elem:
            title_elem = soup.find('h1')
        
        if title_elem:
            title = title_elem.get_text().strip()
            print(f"✅ Title: {title[:50]}...")
        
        # Meta fallback
        if not title:
            meta = soup.find('meta', {'property': 'og:title'})
            if meta:
                title = meta.get('content', '').strip()
        
        if not title:
            title = driver.title.split('|')[0].split('-')[0].strip()
        
        # PRICE
        price = None
        
        # Newegg uses price-current class
        price_elem = soup.find('li', class_='price-current')
        if price_elem:
            # Price is split into dollars and cents
            strong = price_elem.find('strong')
            sup = price_elem.find('sup')
            if strong:
                price_text = strong.get_text()
                if sup:
                    price_text += '.' + sup.get_text()
                price = extract_price(price_text)
        
        # Try item-price
        if not price:
            price_elem = soup.find('div', class_='product-price')
            if price_elem:
                price = extract_price(price_elem.get_text())
        
        # Selenium fallback
        if not price:
            try:
                price_elem = driver.find_element(By.CLASS_NAME, 'price-current')
                price = extract_price(price_elem.text)
            except:
                pass
        
        # Regex fallback
        if not price:
            price_patterns = re.findall(r'\$\s*([\d,]+\.?\d{2})', driver.page_source)
            for match in price_patterns:
                potential_price = extract_price(match)
                if potential_price and 0.99 <= potential_price <= 50000:
                    price = potential_price
                    break
        
        print(f"💰 Price: ${price if price else 'NOT FOUND'}")
        
        if title and price:
            return {
                'title': title[:250],
                'price': price,
                'success': True,
                'error': None
            }
        else:
            return {
                'title': title,
                'price': price,
                'success': False,
                'error': f'Newegg: title={bool(title)}, price={bool(price)}. Check newegg_debug.html'
            }
            
    except Exception as e:
        return {
            'title': None,
            'price': None,
            'success': False,
            'error': f'Newegg error: {str(e)}'
        }


def scrape_aliexpress(driver, url):
    """AliExpress scraper - bulletproof version with JSON extraction"""
    try:
        print("🔍 Scraping AliExpress...")
        time.sleep(6)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # TITLE
        title = None
        for h1 in soup.find_all('h1'):
            text = h1.get_text().strip()
            if len(text) > 10:
                title = text
                break
        
        if not title:
            meta = soup.find('meta', {'property': 'og:title'})
            if meta:
                title = meta.get('content', '').strip()
        
        if not title:
            title = driver.title.replace(' - AliExpress', '').strip()
        
        if not title:
            title = f"AliExpress Product {url.split('/')[-1].split('.')[0].split('?')[0]}"
        
        print(f"📝 Title: {title[:50]}...")
        
        # PRICE - ULTIMATE METHOD: Extract from JavaScript window object
        price = None
        
        # Method 1: Execute JavaScript to get price from window.runParams
        try:
            js_price = driver.execute_script("""
                if (window.runParams && window.runParams.data) {
                    var data = window.runParams.data;
                    if (data.priceModule && data.priceModule.minActivityAmount) {
                        return data.priceModule.minActivityAmount.value;
                    }
                    if (data.priceModule && data.priceModule.minAmount) {
                        return data.priceModule.minAmount.value;
                    }
                }
                return null;
            """)
            
            if js_price:
                price = float(js_price)
                print(f"💰 Price from JS: ${price}")
        except:
            pass
        
        # Method 2: Look in page source for JSON data
        if not price:
            import json
            # Find script tags with JSON data
            scripts = soup.find_all('script')
            for script in scripts:
                script_text = script.string
                if script_text and 'runParams' in script_text:
                    try:
                        # Extract JSON from runParams
                        start = script_text.find('window.runParams')
                        if start > -1:
                            json_start = script_text.find('{', start)
                            json_end = script_text.rfind('}', json_start) + 1
                            json_str = script_text[json_start:json_end]
                            
                            data = json.loads(json_str)
                            
                            # Navigate nested JSON to find price
                            if 'data' in data:
                                price_module = data['data'].get('priceModule', {})
                                
                                # Try different price fields
                                if 'minActivityAmount' in price_module:
                                    price = float(price_module['minActivityAmount']['value'])
                                elif 'minAmount' in price_module:
                                    price = float(price_module['minAmount']['value'])
                                elif 'maxActivityAmount' in price_module:
                                    price = float(price_module['maxActivityAmount']['value'])
                                
                                if price:
                                    print(f"💰 Price from JSON: ${price}")
                                    break
                    except:
                        continue
        
        # Method 3: URL parameter extraction (your previous method)
        if not price:
            import urllib.parse
            parsed_url = urllib.parse.unquote(url)
            
            # Look for price patterns in URL
            url_patterns = [
                r'USD.*?([\d,]+\.?\d{1,2}).*?([\d,]+\.?\d{1,2})',  # Matches "USD 181.96 69.42"
                r'US\s*\$\s*([\d,]+\.?\d{0,2})',
            ]
            
            for pattern in url_patterns:
                matches = re.findall(pattern, parsed_url)
                if matches:
                    if isinstance(matches[0], tuple):
                        # Get second price (sale price)
                        potential_price = extract_price(matches[0][1])
                    else:
                        potential_price = extract_price(matches[0])
                    
                    if potential_price and 1 <= potential_price <= 10000:
                        price = potential_price
                        print(f"💰 Price from URL: ${price}")
                        break
        
        # Method 4: Look for data-spm-anchor-id elements (AliExpress specific)
        if not price:
            price_spans = soup.find_all('span', attrs={'data-spm-anchor-id': True})
            for span in price_spans:
                text = span.get_text().strip()
                if '$' in text or 'USD' in text:
                    potential_price = extract_price(text)
                    if potential_price and 1 <= potential_price <= 10000:
                        price = potential_price
                        print(f"💰 Price from span: ${price}")
                        break
        
        print(f"📊 RESULT - Title: {bool(title)}, Price: ${price if price else 'NOT FOUND'}")
        
        if title and price:
            return {'title': title[:250], 'price': price, 'success': True, 'error': None}
        else:
            # If we got title but no price, return with helpful error
            return {
                'title': title,
                'price': price,
                'success': False,
                'error': f'AliExpress: Found title but could not extract price. The page may use advanced anti-scraping. Try a different product or use AliExpress.com (not .us)'
            }
            
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return {'title': None, 'price': None, 'success': False, 'error': f'AliExpress error: {str(e)}'}

def scrape_generic(driver, url):
    """Generic fallback"""
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        title = soup.find('h1')
        title = title.get_text().strip() if title else None
        
        price = None
        for elem in soup.find_all(class_=re.compile('price', re.I)):
            price = extract_price(elem.get_text())
            if price:
                break
        
        if title and price:
            return {'title': title[:250], 'price': price, 'success': True, 'error': None}
        return {'title': None, 'price': None, 'success': False, 'error': 'Generic scraper failed'}
    except Exception as e:
        return {'title': None, 'price': None, 'success': False, 'error': str(e)}


def extract_price(price_text):
    """Extract price from text"""
    if not price_text:
        return None
    
    price_text = str(price_text).strip()
    matches = re.findall(r'[\d,]+\.?\d*', price_text)
    
    if not matches:
        return None
    
    price_str = matches[0].replace(',', '')
    
    try:
        price = float(price_str)
        if 0.01 <= price <= 999999:
            return round(price, 2)
    except ValueError:
        pass
    
    return None