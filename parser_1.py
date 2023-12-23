from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)  # Включите CORS для всего приложения
conn = sqlite3.connect('products.db')
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        stock_status TEXT,
        article TEXT,
        span_text TEXT,
        url TEXT,
        wilted BOOLEAN,
        gone BOOLEAN
    )
''')
conn.commit()
conn.close()

@app.route('/api/add_product', methods=['POST'])
def add_product():
    try:
        url = request.json['url']
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('h1', class_='product_title').text.strip() if soup.find('h1', class_='product_title') else 'Заголовок не найден'
        stock_status = soup.find('div', class_='stock').text.strip() if soup.find('div', class_='stock') else 'Статус наличия товара не найден'
        article = soup.find('span', class_='sku').text.strip() if soup.find('span', class_='sku') else 'Артикл не найден'
        span_element = soup.find('p', class_='all-more-many')
        span_text = span_element.span.text.strip() if span_element and span_element.span else 'Текст в span не найден'
    
        conn = sqlite3.connect('products.db')
        c = conn.cursor()
        c.execute('SELECT * FROM products WHERE article=?', (article,))
        existing_product = c.fetchone()

        if existing_product:
            # Если запись существует, обновляем stock_status
            c.execute('''
                UPDATE products
                SET stock_status=?, wilted=(stock_status='В наявності' AND ? != 'В наявності'), gone=(stock_status!='В наявності' AND ? = 'В наявності')
                WHERE article=?
            ''', (stock_status,stock_status,stock_status,article))
        else:
            # Если записи нет, добавляем новую запись
            c.execute('''
                INSERT INTO products (title, stock_status, article, span_text, url, wilted, gone)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, stock_status, article, span_text, url, False, False))

        conn.commit()
        conn.close()


        product_data = {
            'title': title,
            'stock_status': stock_status,
            'article': article,
            'span_text': span_text,
            'url': url,
            'wilted': False,  # Изначально устанавливаем в False
            'gone': False, 
        }
        print(product_data)
        return jsonify(product_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    
@app.route('/api/get_products', methods=['GET'])
def get_products():
    try:
        conn = sqlite3.connect('products.db')
        c = conn.cursor()
        c.execute('SELECT * FROM products')
        rows = c.fetchall()
        conn.close()

        products = []
        for row in rows:
            product = {
                'id': row[0],
                'title': row[1],
                'stock_status': row[2],
                'article': row[3],
                'span_text': row[4],
                'url': row[5],
                'wilted': bool(row[6]),  # Преобразовываем значение в boolean
                'gone': bool(row[7]),
            }
            products.append(product)

        return jsonify(products)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)