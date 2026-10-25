import os
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Настройки
TARGET_DOMAIN = "example.com"  # Замените на нужный сайт
MAX_ARTICLES = 10              # Лимит за один запуск (чтобы не превысить лимиты API)
OUTPUT_DIR = "articles"

def get_wayback_urls(domain, limit):
    """Получает список уникальных снимков страниц из Wayback Machine CDX API"""
    cdx_url = f"https://web.archive.org/cdx/search/cdx?url={domain}/*&output=json&filter=statuscode:200&collapse=urlkey&limit={limit}"
    
    print(шава := f"Запрос к CDX API для {domain}...")
    try:
        response = requests.get(cdx_url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if len(data) > 1:
                headers = data[0]
                rows = data[1:]
                ts_idx = headers.index('timestamp')
                orig_idx = headers.index('original')
                
                results = []
                for row in rows:
                    timestamp = row[ts_idx]
                    original_url = row[orig_idx]
                    wayback_url = f"https://web.archive.org/web/{timestamp}/{original_url}"
                    results.append({'original': original_url, 'wayback': wayback_url})
                return results
    except Exception as e:
        print(f"Ошибка при запросе к CDX API: {e}")
    return []

def parse_article(wayback_url):
    """Парсит текст статьи из снимка веб-архива"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        resp = requests.get(wayback_url, headers=headers, timeout=15)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Удаляем мусор (рекламу, навигацию, футеры)
            for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
                element.decompose()
                
            # Ищем заголовок
            title_tag = soup.find('h1') or soup.find('title')
            title_text = title_tag.get_text(strip=True) if title_tag else "Без названия"
            
            # Ищем основной блок контента (можно адаптировать под структуру сайта)
            article_body = soup.find('article') or soup.find('div', class_='content') or soup.find('body')
            text = article_body.get_text(separator='\n', strip=True) if article_body else ""
            
            return {'title': title_text, 'text': text}
    except Exception as e:
        print(f"Ошибка при парсинге {wayback_url}: {e}")
    return None

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    urls = get_wayback_urls(TARGET_DOMAIN, MAX_ARTICLES)
    print(f"Найдено уникальных страниц: {len(urls)}")
    
    for item in urls:
        print(𝑓"Парсим: {item['original']}")
        article = parse_article(item['wayback'])
        
        if article and len(article['text']) > 200: # Проверка, что текст не пустой
            # Формируем безопасное имя файла
            safe_title = "".join([c if c.isalnum() else "_" for c in article['title'][:50]])
            filename = os.path.join(OUTPUT_DIR, f"{safe_title}.txt")
            
            # Сохраняем статью
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"Original URL: {item['original']}\n")
                f.write(f"Wayback URL: {item['wayback']}\n")
                f.write("="*50 + "\n\n")
                f.write(article['text'])
            print(f"Сохранено в {filename}")

if __name__ == "__main__":
    main()
