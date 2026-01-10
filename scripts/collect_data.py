import os
import datetime
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import pytz
from dotenv import load_dotenv

# Configuration
load_dotenv()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
MINKABU_URL = "https://minkabu.jp/financial_item_ranking/fall?exchange=tokyo.prime&order=asc"
MINKABU_BUY_URL = "https://minkabu.jp/financial_item_ranking/buy_picks_rise?exchange=tokyo&order=desc"
KABUTAN_URL = "https://kabutan.jp/info/accessranking/2_1"
OUTPUT_DIR = "src/content/blog"

def get_current_date():
    jst = pytz.timezone('Asia/Tokyo')
    return datetime.datetime.now(jst)

def fetch_minkabu_data():
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(MINKABU_URL, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # This selector might need adjustment based on actual site structure
        # Simplified extraction logic for demonstration
        rankings = []
        rows = soup.select('table.md_table_theme01 tr')
        for row in rows[:11]: # Top 10 (skipping header if any, or just taking first few)
            cols = row.find_all('td')
            if len(cols) >= 3:
                name = cols[1].get_text(strip=True)
                code = cols[1].find('a').get('href').split('/')[-1] if cols[1].find('a') else "N/A"
                change = cols[3].get_text(strip=True)
                rankings.append(f"{code} {name}: {change}")
        return "\n".join(rankings)
    except Exception as e:
        print(f"Error fetching Minkabu data: {e}")
        return "Failed to fetch Minkabu rankings."

def fetch_minkabu_buy_data():
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(MINKABU_BUY_URL, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        rankings = []
        # The structure is likely similar to the other ranking page
        rows = soup.select('table.md_table_theme01 tr')
        for row in rows[:11]: # Top 10
            cols = row.find_all('td')
            if len(cols) >= 3:
                name = cols[1].get_text(strip=True)
                code = cols[1].find('a').get('href').split('/')[-1] if cols[1].find('a') else "N/A"
                # For buy picks, column index might differ, but assuming standard layout for now or grabbing what we can
                # Often col 2 or 3 has the relevant score/change
                rankings.append(f"{code} {name}")
        return "\n".join(rankings)
    except Exception as e:
        print(f"Error fetching Minkabu Buy Picks data: {e}")
        return "Failed to fetch Minkabu Buy Picks."

def fetch_kabutan_data():
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(KABUTAN_URL, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        news_items = []
        links = soup.select('table.s_news_list tr td a')
        for link in links[:5]:
            title = link.get_text(strip=True)
            url = "https://kabutan.jp" + link.get('href')
            news_items.append(f"- [{title}]({url})")
        return "\n".join(news_items)
    except Exception as e:
        print(f"Error fetching Kabutan data: {e}")
        return "Failed to fetch Kabutan news."

def generate_blog_post(date, market_data, buy_data, news_data):
    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY not found.")
        return None

    genai.configure(api_key=GEMINI_API_KEY)
    
    # Try valid models from the user's available list
    models_to_try = [
        'gemini-2.0-flash', 
        'gemini-2.0-flash-lite', 
        'gemini-3-flash-preview',
        'gemini-2.0-flash-exp'
    ]
    
    model = None
    for model_name in models_to_try:
        try:
            print(f"Attempting to use model: {model_name}")
            model = genai.GenerativeModel(model_name)
            # Test if model works by generating a small token (not consuming much quota)
            # Or just proceed to generate content. If it fails, catch and try next.
            
            prompt = f"""
            You are a financial analyst writing a daily blog post about the Japanese stock market.
            Date: {date.strftime('%Y-%m-%d')}
            
            Market Data (Top Fallers):
            {market_data}

            Undervalued/Buy Picks Rise Ranking (Might indicate undervalued stocks):
            {buy_data}
            
            Popular News:
            {news_data}
            
            Write a blog post in Japanese in Markdown format.
            The post should analyze why these stocks fell and comment on the popular news.
            Also, pick 1-2 stocks from the Buy Picks ranking and analyze why they might be considered undervalued or gathering attention.
            Make it engaging and informative.
            
            Structure:
            1. Title (H1)
            2. Introduction
            3. Today's Market Drop Ranking (Analyze top 3-5)
            4. Undervalued Stocks Watch (Analyze Buy Picks)
            5. Attention News
            6. Conclusion
            
            Output only the Markdown content (starting with frontmatter).
            Frontmatter format:
            ---
            title: "TITLE_HERE"
            description: "DESCRIPTION_HERE"
            pubDate: "{date.strftime('%Y-%m-%d')}"
            ---
            """
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Model {model_name} failed: {e}")
            continue

    print("All models failed. Listing available models:")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(m.name)
    except Exception as e:
        print(f"Failed to list models: {e}")
        
    return None

def main():
    date = get_current_date()
    print(f"Starting data collection for {date.isoformat()}")
    
    minkabu_data = fetch_minkabu_data()
    minkabu_buy_data = fetch_minkabu_buy_data()
    kabutan_data = fetch_kabutan_data()
    
    content = generate_blog_post(date, minkabu_data, minkabu_buy_data, kabutan_data)
    
    if content:
        # Clean up code blocks if Gemini returns them
        if content.startswith("```markdown"):
            content = content.replace("```markdown", "", 1)
        if content.startswith("```"):
            content = content.replace("```", "", 1)
        if content.endswith("```"):
             content = content[:-3]
             
        filename = f"{OUTPUT_DIR}/{date.strftime('%Y-%m-%d')}-stock-report.md"
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content.strip())
        print(f"Successfully created {filename}")
    else:
        print("Failed to generate content.")

if __name__ == "__main__":
    main()
