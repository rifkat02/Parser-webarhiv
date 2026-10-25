import os
import random
import re
import requests
from bs4 import BeautifulSoup
from langdetect import detect, DetectorFactory

# Фиксируем seed для стабильной работы langdetect
DetectorFactory.seed = 0

# Настройки
MAX_ARTICLES_PER_RUN = 3  # Сколько статей сохранять за один запуск
OUTPUT_DIR = "articles"

# Список популярных русскоязычных платформ и СМИ в веб-архиве
DOMAINS = [
    "habr.com", "vc.ru", "pikabu.ru", "lenta.ru", 
    "ria.ru", "gazeta.ru", "kommersant.ru", "argumenti.ru"
]

def get_wayback_urls_for_domain(domain):
    """Получает снимки страниц из веб-архива для конкретного домена за случайный год"""
    random_year = random.randint(2012, 2021)
    cdx_url = (
        f"https://web.archive.org/cdx/search/cdx?"
        f"url={domain}/*&from={random_year}0101&to={random_year}1231"
        f"&output=json&filter=statuscode:200&filter=mimetype:text/html"
        f"&collapse=urlkey&limit=30"
    )
    
    print(f"Запрос к CDX API для домена {domain} ({random_year} год)...")
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
                print(f"Найдено ссылок для {domain}: {len(results)}")
                return results
    except Exception as e:
        print(f"Ошибка при запросе CDX API: {e}")
    return []

def extract_article_content(wayback_url):
    """Скачивает страницу и извлекает чистый текст статьи"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        resp = requests.get(wayback_url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return None
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Удаляем мусор, скрипты, рекламу, шапки и панели веб-архива
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe", "noscript"]):
            tag.decompose()
        
        for wm_tag in soup.find_all(id=re.compile(r'wm-.*|wm-ipp.*')):
            wm_tag.decompose()

        # Ищем заголовок
        title_tag = soup.find('h1') or soup.find('title')
        title = title_tag.get_text(strip=True) if title_tag else "Без названия"

        # Собираем абзацы текста
        paragraphs = [p.get_text(strip=True) for p in soup.find_all('p') if len(p.get_text(strip=True)) > 30]
        text = "\n\n".join(paragraphs)

        # Проверка минимальной длины текста (не менее 400 символов)
        if len(text) < 400:
            return None

        # Проверка языка (должен быть русский)
        try:
            lang = detect(text[:1000])
            if lang != 'ru':
                return None
        except Exception:
            return None

        return {'title': title, 'text': text}

    except Exception as e:
        print(f"Ошибка при парсинге страницы: {e}")
        return None

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    saved_count = 0
    
    # Перемешиваем список доменов для разнообразия
    shuffled_domains = DOMAINS.copy()
    random.shuffle(shuffled_domains)

    for domain in shuffled_domains:
        if saved_count >= MAX_ARTICLES_PER_RUN:
            break
            
        urls = get_wayback_urls_for_domain(domain)
        for item in urls:
            if saved_count >= MAX_ARTICLES_PER_RUN:
                break
                
            print(f"Проверяем URL: {item['original']}")
            article = extract_article_content(item['wayback'])
            
            if article:
                # Очищаем заголовок для имени файла
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

                print(f" -> УСПЕШНО СОХРАНЕНО: {filepath}")
                saved_count += 1

    print(f"\nГотово! Всего сохранено новых статей: {saved_count}")

if __name__ == "__main__":
    main()
