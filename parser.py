import os
import random
import re
import requests
from bs4 import BeautifulSoup
from langdetect import detect, DetectorFactory

# Фиксируем seed для стабильной работы langdetect
DetectorFactory.seed = 0

# Настройки
MAX_ARTICLES_PER_RUN = 5  # Сколько русскоязычных статей сохранить за один запуск
OUTPUT_DIR = "articles"

# Шаблоны для генерации случайных поисковых запросов в зоне .ru
SEARCH_PATTERNS = [
    "ru/*", "ru/article/*", "ru/blog/*", "ru/news/*", 
    "ru/stati/*", "ru/posts/*", "ru/paper/*", "ru/entry/*"
]

def get_random_wayback_urls(limit_fetch=30):
    """Генерирует случайные ссылки из веб-архива в зоне .ru"""
    pattern = random.choice(SEARCH_PATTERNS)
    random_offset = random.randint(0, 1000)
    
    cdx_url = (
        f"https://web.archive.org/cdx/search/cdx?"
        f"url=*.{pattern}&output=json&filter=statuscode:200"
        f"&filter=mimetype:text/html&collapse=urlkey"
        f"&limit={limit_fetch}&offset={random_offset}"
    )
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        response = requests.get(cdx_url, headers=headers, timeout=20)
        if response.status_code == 200:
            data = response.json()
            if len(data) > 1:
                headers_list = data[0]
                rows = data[1:]
                ts_idx = headers_list.index('timestamp')
                orig_idx = headers_list.index('original')
                
                results = []
                for row in rows:
                    timestamp = row[ts_idx]
                    original_url = row[orig_idx]
                    wayback_url = f"https://web.archive.org/web/{timestamp}/{original_url}"
                    results.append({'original': original_url, 'wayback': wayback_url})
                
                random.shuffle(results)
                return results
    except Exception as e:
        print(f"Ошибка обращения к CDX API: {e}")
    return []

def extract_article_content(wayback_url):
    """Скачивает страницу, очищает и проверяет язык"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        resp = requests.get(wayback_url, headers=headers, timeout=20)
        if resp.status_code != 200:
            return None
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Удаляем мусор, скрипты, панели веб-архива
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe", "noscript"]):
            tag.decompose()
        
        for wm_tag in soup.find_all(id=re.compile(r'wm-.*|wm-ipp.*')):
            wm_tag.decompose()

        # Заголовок
        title_tag = soup.find('h1') or soup.find('title')
        title = title_tag.get_text(strip=True) if title_tag else "Без названия"

        # Текст
        paragraphs = [p.get_text(strip=True) for p in soup.find_all('p') if len(p.get_text(strip=True)) > 40]
        text = "\n\n".join(paragraphs)

        if len(text) < 300:
            return None

        # Проверка на русский язык
        try:
            lang = detect(text[:1000])
            if lang != 'ru':
                return None
        except Exception:
            return None

        return {'title': title, 'text': text}

    except Exception as e:
        print(f"Ошибка при парсинге {wayback_url}: {e}")
        return None

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    saved_count = 0
    attempts = 0
    
    print("Ищем случайные статьи на русском языке в Веб-Архиве...")

    while saved_count < MAX_ARTICLES_PER_RUN and attempts < 3:
        attempts += 1
        urls = get_random_wayback_urls(limit_fetch=40)
        
        for item in urls:
            if saved_count >= MAX_ARTICLES_PER_RUN:
                break
                
            print(f"Проверяем: {item['original']}")
            article = extract_article_content(item['wayback'])
            
            if article:
                clean_title = re.sub(r'[^\w\s-]', '', article['title'])[:40].strip()
                safe_name = clean_title if clean_title else f"article_{random.randint(1000, 9999)}"
                filepath = os.path.join(OUTPUT_DIR, f"{safe_name}.txt")
                
                if os.path.exists(filepath):
                    filepath = os.path.join(OUTPUT_DIR, f"{safe_name}_{random.randint(100, 999)}.txt")

                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(f"Заголовок: {article['title']}\n")
                    f.write(f"Оригинальный URL: {item['original']}\n")
                    f.write(f"Архивный URL: {item['wayback']}\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(article['text'])

                print(f" -> СОХРАНЕНО: {filepath}")
                saved_count += 1

    print(f"\nГотово! Сохранено статей на русском языке: {saved_count}")

if __name__ == "__main__":
    main()
