import os
import re
import requests
from bs4 import BeautifulSoup

OUTPUT_DIR = "articles"

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("Запуск парсера Веб-архива...")
    
    # Запрос к CDX API для получения сохраненных постов
    cdx_url = "https://web.archive.org/cdx/search/cdx?url=habr.com/ru/post/*&output=json&limit=15&filter=statuscode:200"
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        print("Отправка запроса к CDX API...")
        response = requests.get(cdx_url, headers=headers, timeout=20)
        print(f"Статус ответа API: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Найдено записей: {len(data) - 1 if len(data) > 0 else 0}")
            
            if len(data) > 1:
                headers_list = data[0]
                rows = data[1:]
                ts_idx = headers_list.index('timestamp')
                orig_idx = headers_list.index('original')
                
                # Берем первую успешную для теста
                for i, row in enumerate(rows):
                    timestamp = row[ts_idx]
                    original_url = row[orig_idx]
                    wayback_url = f"https://web.archive.org/web/{timestamp}/{original_url}"
                    
                    print(f"Пробуем скачать: {wayback_url}")
                    page_resp = requests.get(wayback_url, headers=headers, timeout=15)
                    
                    if page_resp.status_code == 200:
                        soup = BeautifulSoup(page_resp.text, 'html.parser')
                        
                        # Удаляем мусор
                        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                            tag.decompose()
                            
                        title_tag = soup.find('h1') or soup.find('title')
                        title_text = title_tag.get_text(strip=True) if title_tag else f"Статья_{i}"
                        
                        # Собираем текст
                        body_text = soup.get_text(separator='\n', strip=True)
                        lines = [line for line in body_text.split('\n') if len(line.strip()) > 15]
                        clean_text = "\n".join(lines[:40]) # Первые 40 строк контента
                        
                        if len(clean_text) > 100:
                            # Очищаем имя файла
                            safe_title = re.sub(r'[^\w\s-]', '', title_text)[:30].strip() or f"article_{i}"
                            filepath = os.path.join(OUTPUT_DIR, f"{safe_title}.txt")
                            
                            with open(filepath, "w", encoding="utf-8") as f:
                                f.write(f"Оригинал: {original_url}\n")
                                f.write(f"Архив: {wayback_url}\n")
                                f.write("="*50 + "\n\n")
                                f.write(clean_text)
                                
                            print(f"УСПЕШНО СОХРАНЕНО: {filepath}")
                            break # Сохранили одну статью и завершаем работу
                            
        print("Парсер завершил работу.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    main()
