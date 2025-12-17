import requests
from bs4 import BeautifulSoup
import re
import random

def scrape_product(url):
    """
    Smart router: Selenium for JS sites, requests for static sites
    """
    # AliExpress needs Selenium
    if 'aliexpress' in url.lower():
        from utils.selenium_scraper import scrape_with_selenium
        print("🤖 Using Selenium for AliExpress")
        return scrape_with_selenium(url)
    
    # Everyone else: fast requests
    print(f"⚡ Using requests for {url}")
    return scrape_with_requests(url)


def scrape_with_requests(url):
    """Fast scraping with requests + rotating headers"""
    try:
        headers = get_random_headers()
        
        print(f"📡 Fetching {url[:50]}...")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        print(f"✅ Got response ({len(response.content)} bytes)")
        
        # Route to site-specific parser
        if 'walmart' in url.lower():
            return parse_walmart(response.content, url)
        elif 'bestbuy' in url.lower():
            return parse_bestbuy(response.content, url)
        elif 'newegg' in url.lower():
            return parse_newegg(response.content, url)
        else:
            return parse_generic(response.content, url)
            
    except requests.exceptions.RequestException as e:
        return {
            'title': None,
            'price': None,
            'success': False,
            'error': f'Request failed: {str(e)}'
        }
    except Exception as e:
        return {
            'title': None,
            'price': None,
            'success': False,
            'error': f'Scraping error: {str(e)}'
        }


def get_random_headers():
    """Rotate user agents to avoid detection"""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]
    
    return {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }


def parse_walmart(html_content, url):
    """Parse Walmart HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Save debug
    with open('walmart_debug.html', 'w', encoding='utf-8') as f:
        f.write(str(soup))
    print("📄 Saved walmart_debug.html")
    
    # Title
    title = None
    title_elem = soup.find('h1', {'itemprop': 'name'})
    if not title_elem:
        title_elem = soup.find('h1')
    if not title_elem:
        meta = soup.find('meta', {'property': 'og:title'})
        if meta:
            title = meta.get('content', '')
    
    if title_elem:
        title = title_elem.get_text().strip()
    
    print(f"📝 Title: {title[:50] if title else 'NOT FOUND'}...")
    
    # Price
    price = None
    
    # Try itemprop
    price_elem = soup.find('span', {'itemprop': 'price'})
    if price_elem:
        price = extract_price(price_elem.get('content') or price_elem.get_text())
    
    # Try data-price
    if not price:
        price_elem = soup.find(attrs={'data-price': True})
        if price_elem:
            price = extract_price(price_elem.get('data-price'))
    
    # Regex search
    if not price:
        price_patterns = re.findall(r'"price"[:\s]+"?([\d,]+\.?\d{0,2})"?', str(html_content))
        for match in price_patterns:
            potential = extract_price(match)
            if potential and 0.99 <= potential <= 50000:
                price = potential
                break
    
    print(f"💰 Price: ${price if price else 'NOT FOUND'}")
    
    if title and price:
        return {'title': title[:250], 'price': price, 'success': True, 'error': None}
    else:
        return {
            'title': title,
            'price': price,
            'success': False,
            'error': f'Walmart: title={bool(title)}, price={bool(price)}. Check walmart_debug.html'
        }


def parse_bestbuy(html_content, url):
    """Parse BestBuy HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    with open('bestbuy_debug.html', 'w', encoding='utf-8') as f:
        f.write(str(soup))
    print("📄 Saved bestbuy_debug.html")
    
    # Title
    title = None
    title_elem = soup.find('h1')
    if title_elem:
        title = title_elem.get_text().strip()
    
    if not title:
        meta = soup.find('meta', {'property': 'og:title'})
        if meta:
            title = meta.get('content', '')
    
    print(f"📝 Title: {title[:50] if title else 'NOT FOUND'}...")
    
    # Price - BestBuy embeds in JSON
    price = None
    
    # Look in script tags for JSON data
    scripts = soup.find_all('script', {'type': 'application/ld+json'})
    for script in scripts:
        try:
            import json
            data = json.loads(script.string)
            if isinstance(data, dict) and 'offers' in data:
                price = extract_price(str(data['offers'].get('price', '')))
                if price:
                    break
        except:
            continue
    
    # Regex fallback
    if not price:
        price_patterns = re.findall(r'"price"[:\s]+([\d,]+\.?\d{0,2})', str(html_content))
        for match in price_patterns:
            potential = extract_price(match)
            if potential and 9.99 <= potential <= 50000:
                price = potential
                break
    
    print(f"💰 Price: ${price if price else 'NOT FOUND'}")
    
    if title and price:
        return {'title': title[:250], 'price': price, 'success': True, 'error': None}
    else:
        return {
            'title': title,
            'price': price,
            'success': False,
            'error': f'BestBuy: title={bool(title)}, price={bool(price)}. Check bestbuy_debug.html'
        }


def parse_newegg(html_content, url):
    """Parse Newegg HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    with open('newegg_debug.html', 'w', encoding='utf-8') as f:
        f.write(str(soup))
    print("📄 Saved newegg_debug.html")
    
    # Title
    title = None
    title_elem = soup.find('h1', class_='product-title')
    if not title_elem:
        title_elem = soup.find('h1')
    
    if title_elem:
        title = title_elem.get_text().strip()
    
    if not title:
        meta = soup.find('meta', {'property': 'og:title'})
        if meta:
            title = meta.get('content', '')
    
    print(f"📝 Title: {title[:50] if title else 'NOT FOUND'}...")
    
    # Price
    price = None
    price_elem = soup.find('li', class_='price-current')
    if price_elem:
        price_text = price_elem.get_text()
        price = extract_price(price_text)
    
    # JSON fallback
    if not price:
        scripts = soup.find_all('script', {'type': 'application/ld+json'})
        for script in scripts:
            try:
                import json
                data = json.loads(script.string)
                if 'offers' in data:
                    price = extract_price(str(data['offers'].get('price', '')))
                    if price:
                        break
            except:
                continue
    
    print(f"💰 Price: ${price if price else 'NOT FOUND'}")
    
    if title and price:
        return {'title': title[:250], 'price': price, 'success': True, 'error': None}
    else:
        return {
            'title': title,
            'price': price,
            'success': False,
            'error': f'Newegg: title={bool(title)}, price={bool(price)}. Check newegg_debug.html'
        }


def parse_generic(html_content, url):
    """Generic fallback parser"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    title = None
    title_elem = soup.find('h1')
    if title_elem:
        title = title_elem.get_text().strip()
    
    price = None
    price_elems = soup.find_all(class_=re.compile('price', re.I))
    for elem in price_elems:
        price = extract_price(elem.get_text())
        if price:
            break
    
    if title and price:
        return {'title': title[:250], 'price': price, 'success': True, 'error': None}
    else:
        return {'title': None, 'price': None, 'success': False, 'error': 'Generic scraper failed'}


def extract_price(price_text):
    """Extract numeric price from text"""
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