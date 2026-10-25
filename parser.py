import os
import requests
from bs4 import BeautifulSoup

OUTPUT_DIR = "articles"

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("Запуск тестового скачивания из Веб-архива...")
    
    # Прямая ссылка на архивную копию страницы Хабра за 2021 год
    wayback_url = "https://web.archive.org/web/20211001000000/https://habr.com/ru/all/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        print(f"Запрос к архиву: {wayback_url}")
        resp = requests.get(wayback_url, headers=headers, timeout=25)
        print(f"Статус ответа: {resp.status_code}")
        
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Убираем лишние теги
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()
                
            title_tag = soup.find('h1') or soup.find('title')
            title_text = title_tag.get_text(strip=True) if title_tag else "Архивная статья"
            
            body_text = soup.get_text(separator='\n', strip=True)
            lines = [line for line in body_text.split('\n') if len(line.strip()) > 20]
            clean_text = "\n".join(lines[:50])
            
            filepath = os.path.join(OUTPUT_DIR, "habr_archive_test.txt")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"Оригинал: https://habr.com/ru/all/\n")
                f.write(f"Архив: {wayback_url}\n")
                f.write("="*50 + "\n\n")
                f.write(clean_text if len(clean_text) > 50 else "Текст страницы успешно получен, но оказался пустым.")
                
            print(f"Файл успешно сохранен: {filepath}")
        else:
            create_fallback_file(f"Архив вернул код ответа: {resp.status_code}")
            
    except Exception as e:
        print(f"Произошла ошибка при запросе: {e}")
        create_fallback_file(f"Ошибка: {str(e)}")

def create_fallback_file(message):
    """Создает резервный файл, чтобы папка точно появилась в репозитории"""
    filepath = os.path.join(OUTPUT_DIR, "parser_status.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"Парсер отработал на GitHub Actions.\nСтатус: {message}\n")
    print(f"Создан резервный файл: {filepath}")

if __name__ == "__main__":
    main()
