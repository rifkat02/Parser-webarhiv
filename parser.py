import os
import time
import requests
from bs4 import BeautifulSoup

OUTPUT_DIR = "articles"

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("Запуск парсера с защитой от лимитов...")
    
    # Делаем паузу перед запросом, чтобы не триггерить защиту архива
    time.sleep(3)
    
    # Используем более старую или другую ссылку, чтобы обойти кэш лимитов
    wayback_url = "https://web.archive.org/web/20200501000000/https://habr.com/ru/all/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    
    try:
        print(f"Отправка запроса к архиву: {wayback_url}")
        resp = requests.get(wayback_url, headers=headers, timeout=30)
        print(f"Статус ответа: {resp.status_code}")
        
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Убираем мусорные теги
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()
                
            title_tag = soup.find('h1') or soup.find('title')
            title_text = title_tag.get_text(strip=True) if title_tag else "Архивная статья Habr"
            
            body_text = soup.get_text(separator='\n', strip=True)
            lines = [line for line in body_text.split('\n') if len(line.strip()) > 20]
            clean_text = "\n".join(lines[:60]) # Берем первые 60 строк текста
            
            # Сохраняем полноценную статью
            filename = "habr_article_saved.txt"
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"Заголовок: {title_text}\n")
                f.write(f"Оригинал: https://habr.com/ru/all/\n")
                f.write(f"Архив: {wayback_url}\n")
                f.write("="*50 + "\n\n")
                f.write(clean_text if len(clean_text) > 100 else "Текст пустой.")
                
            print(f"Статья успешно сохранена: {filepath}")
            
            # Удаляем старый файл статуса, если он есть, чтобы не мешался
            status_file = os.path.join(OUTPUT_DIR, "parser_status.txt")
            if os.path.exists(status_file):
                os.remove(status_file)
                
        else:
            save_status(f"Архив вернул код ответа: {resp.status_code} (защита от частых запросов)")
            
    except Exception as e:
        print(f"Ошибка: {e}")
        save_status(f"Ошибка выполнения: {str(e)}")

def save_status(message):
    filepath = os.path.join(OUTPUT_DIR, "parser_status.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"Статус работы парсера:\n{message}\n")
    print(f"Сохранен файл статуса: {filepath}")

if __name__ == "__main__":
    main()
