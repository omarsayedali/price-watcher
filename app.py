from flask import Flask, request, jsonify, render_template
from models import db, Product, PriceHistory
from config import Config
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()
    print("✅ Database tables created successfully!")

# Background scheduler for auto re-scrape
def auto_rescrape_all():
    """Background job to re-scrape all products"""
    with app.app_context():
        from utils.scraper import scrape_product
        
        print("🔄 AUTO RE-SCRAPE: Starting...")
        products = Product.query.all()
        
        for product in products:
            try:
                print(f"🔍 Re-scraping: {product.title[:30]}...")
                result = scrape_product(product.url)
                
                if result['success']:
                    product.current_price = result['price']
                    
                    new_history = PriceHistory(
                        product_id=product.id,
                        price=result['price'],
                        scraped_at=datetime.utcnow()
                    )
                    db.session.add(new_history)
                    print(f"✅ Updated: ${result['price']}")
                else:
                    print(f"❌ Failed: {result['error']}")
                    
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                continue
        
        db.session.commit()
        print("🔄 AUTO RE-SCRAPE: Complete!")

# Initialize and start scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=auto_rescrape_all, trigger="interval", hours=24)
scheduler.start()
print("🔄 Background scheduler started (re-scrapes every 24 hours)")

@app.route('/')
def index():
    return render_template('dashboard.html')


@app.route('/add-product', methods=['POST'])
def add_product():
    """Add or update a product by scraping its URL"""
    try:
        from utils.scraper import scrape_product
        
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({
                'success': False,
                'error': 'URL is required in JSON body'
            }), 400
        
        url = data['url'].strip()
        
        if not url:
            return jsonify({
                'success': False,
                'error': 'URL cannot be empty'
            }), 400
        
        print(f"🔍 Scraping: {url}")
        scrape_result = scrape_product(url)
        
        if not scrape_result['success']:
            return jsonify({
                'success': False,
                'error': scrape_result['error']
            }), 400
        
        title = scrape_result['title']
        price = scrape_result['price']
        
        print(f"✅ Scraped: {title} - ${price}")
        
        existing_product = Product.query.filter_by(url=url).first()
        
        if existing_product:
            print(f"📦 Product exists (ID: {existing_product.id}). Updating...")
            
            existing_product.current_price = price
            existing_product.title = title
            
            new_history = PriceHistory(
                product_id=existing_product.id,
                price=price,
                scraped_at=datetime.utcnow()
            )
            db.session.add(new_history)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Product updated successfully',
                'product': {
                    'id': existing_product.id,
                    'title': existing_product.title,
                    'url': existing_product.url,
                    'current_price': existing_product.current_price,
                    'price_history_count': len(existing_product.price_history)
                }
            }), 200
        
        else:
            print(f"🆕 New product. Creating...")
            
            new_product = Product(
                url=url,
                title=title,
                current_price=price,
                created_at=datetime.utcnow()
            )
            db.session.add(new_product)
            db.session.flush()
            
            first_history = PriceHistory(
                product_id=new_product.id,
                price=price,
                scraped_at=datetime.utcnow()
            )
            db.session.add(first_history)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Product added successfully',
                'product': {
                    'id': new_product.id,
                    'title': new_product.title,
                    'url': new_product.url,
                    'current_price': new_product.current_price,
                    'price_history_count': 1
                }
            }), 201
    
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@app.route('/products', methods=['GET'])
def get_products():
    """Get all tracked products with trends"""
    products = Product.query.all()
    
    return jsonify({
        'success': True,
        'count': len(products),
        'products': [{
            'id': p.id,
            'title': p.title,
            'url': p.url,
            'current_price': p.current_price,
            'created_at': p.created_at.isoformat(),
            'price_history_count': len(p.price_history),
            'price_trend': p.get_price_trend(),
            'price_change_percent': p.get_price_change_percent()
        } for p in products]
    }), 200


@app.route('/product/<int:product_id>/history', methods=['GET'])
def get_price_history(product_id):
    """Get price history for a specific product"""
    product = Product.query.get_or_404(product_id)
    
    history = PriceHistory.query.filter_by(product_id=product_id).order_by(PriceHistory.scraped_at.desc()).all()
    
    return jsonify({
        'success': True,
        'product': {
            'id': product.id,
            'title': product.title,
            'url': product.url,
            'current_price': product.current_price
        },
        'history': [{
            'price': h.price,
            'scraped_at': h.scraped_at.isoformat()
        } for h in history]
    }), 200


@app.route('/delete-product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete a tracked product"""
    try:
        product = Product.query.get_or_404(product_id)
        
        PriceHistory.query.filter_by(product_id=product_id).delete()
        
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Deleted {product.title}'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/rescrape/<int:product_id>', methods=['POST'])
def rescrape_product(product_id):
    """Manually re-scrape a product"""
    try:
        from utils.scraper import scrape_product
        
        product = Product.query.get_or_404(product_id)
        
        result = scrape_product(product.url)
        
        if result['success']:
            product.current_price = result['price']
            product.title = result['title']
            
            new_history = PriceHistory(
                product_id=product.id,
                price=result['price'],
                scraped_at=datetime.utcnow()
            )
            db.session.add(new_history)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Re-scraped successfully',
                'new_price': result['price']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)