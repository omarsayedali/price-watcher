# 📊 Price Watcher

**Full-stack price tracking system with automated scraping and real-time analytics**

Track product prices across Walmart and AliExpress. Get instant alerts on price drops. Visualize historical data.

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-316192?logo=postgresql)](https://www.postgresql.org/)

🚀 **[Live Demo](https://price-watcher-production.up.railway.app/)** • 📖 **[Documentation](#features)**

---

## ✨ Features

- ⚡ **Multi-Platform Scraping** - Walmart & AliExpress support
- 📈 **Price Trend Analysis** - Track up/down changes with percentages
- 🔄 **Auto Updates** - Background re-scraping every 24 hours
- 📊 **Interactive Charts** - Visualize price history with Chart.js
- 🗑️ **Full CRUD** - Add, view, update, and delete tracked products
- 🌙 **Premium Dark UI** - Modern glassmorphism design
- 🔔 **Manual Refresh** - Re-scrape any product on demand

---

## 🛠️ Tech Stack

**Backend**
- Flask 3.0 (REST API)
- PostgreSQL 15 (Database)
- SQLAlchemy 3.1 (ORM)
- APScheduler (Background tasks)

**Scraping**
- Selenium + undetected-chromedriver (JavaScript sites)
- Requests + BeautifulSoup4 (Static sites)

**Frontend**
- Jinja2 Templates
- Chart.js (Visualizations)
- Lucide Icons
- Custom CSS (Dark theme)





## 🚀 Quick Start

### Prerequisites
```bash
Python 3.11+
PostgreSQL 15+
Chrome browser
```

### Installation

```bash
# Clone repository
git clone https://github.com/omarsayedali/price-watcher.git
cd price-watcher

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up database
createdb pricewatcher_db

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Run application
python app.py
```

Open browser to `http://localhost:5001`

---

## 📡 API Reference

### Add Product
```http
POST /add-product
Content-Type: application/json

{
  "url": "https://www.walmart.com/ip/..."
}
```

### Get All Products
```http
GET /products
```

### Get Price History
```http
GET /product/{id}/history
```

### Re-scrape Product
```http
POST /rescrape/{id}
```

### Delete Product
```http
DELETE /delete-product/{id}
```

---

## 🏗️ Architecture

### Database Schema

**Product**
- `id` (Primary Key)
- `url` (Unique)
- `title`
- `current_price`
- `created_at`

**PriceHistory**
- `id` (Primary Key)
- `product_id` (Foreign Key → Product)
- `price`
- `scraped_at`

**Relationship**: One Product → Many PriceHistory entries

### Scraping Strategy

1. **URL Detection** - Identifies Walmart or AliExpress
2. **Site-Specific Logic**:
   - **Walmart**: Fast requests + BeautifulSoup
   - **AliExpress**: Selenium with JavaScript execution
3. **Price Extraction** - Multiple fallback methods
4. **Database Storage** - Save to PostgreSQL with timestamp

### Background Jobs

```python
# APScheduler runs this every 24 hours
def auto_rescrape_all():
    for product in Product.query.all():
        new_price = scrape_product(product.url)
        save_to_price_history(product, new_price)
```

---

## 📁 Project Structure

```
price_watcher/
├── app.py                    # Flask app + routes
├── models.py                 # Database models
├── config.py                 # Configuration
├── requirements.txt          # Dependencies
├── .env.example              # Environment template
├── utils/
│   ├── scraper.py            # Requests scraper
│   └── selenium_scraper.py   # Selenium scraper
└── templates/
    └── dashboard.html        # Frontend UI
```

---

## ⚙️ Configuration

### Environment Variables

Create `.env` file:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/pricewatcher_db
SECRET_KEY=your-secret-key-here
```

### Scraping Settings

Edit `utils/scraper.py`:
- **Timeout**: 15 seconds (configurable)
- **Re-scrape interval**: 24 hours (in `app.py`)
- **User agents**: Rotates randomly

---

## 🚢 Deployment

### Railway

```bash
# Connect GitHub repo to Railway
# Set environment variables in Railway dashboard
# Deploy automatically on push to main
```

### Docker

```bash
docker build -t price-watcher .
docker run -p 5001:5001 --env-file .env price-watcher
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Database connection failed | Check PostgreSQL is running: `pg_ctl status` |
| Scraping failed | Site may be blocking. Try different URL |
| Port 5000 in use | Change port in `app.py` to 5001 |
| ChromeDriver error | Update Chrome browser to latest version |

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/name`)
3. Commit changes (`git commit -m 'Add feature'`)
4. Push to branch (`git push origin feature/name`)
5. Open Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file

---

## 👤 Author

**Omar Sayed Ali**

- GitHub: [@omarsayedali](https://github.com/omarsayedali)
- Email: your.email@example.com

---

## 🎯 Roadmap

- [ ] Add Amazon, eBay, Newegg support
- [ ] Email/SMS price drop alerts
- [ ] User authentication
- [ ] CSV export
- [ ] Mobile app (React Native)
- [ ] Chrome extension
- [ ] ML price prediction

---

## 📊 Stats

- **Lines of Code**: ~1,500
- **API Endpoints**: 6
- **Supported Sites**: 2
- **Database Tables**: 2
- **Development Time**: 2 weeks

---

## 🙏 Acknowledgments

- Flask & SQLAlchemy communities
- Selenium contributors
- Chart.js for visualizations
- Lucide Icons

---

<div align="center">

**⭐ Star this repo if you find it useful!**

Built with 🔥 by [Omar](https://github.com/omarsayedali)

</div>
