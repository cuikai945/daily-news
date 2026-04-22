import feedparser
import json
import os
import requests
import google.generativeai as genai

# 设置 8 大平台源 (已替换为联合早报)
FEEDS = {
    'FT中文网': 'http://www.ftchinese.com/rss/news',
    'BBC': 'http://feeds.bbci.co.uk/zhongwen/simp/rss.xml',
    '纽约时报': 'https://cn.nytimes.com/rss/',
    '华尔街日报': 'https://cn.wsj.com/zh-hans/rss',
    '36氪': 'https://36kr.com/feed',
    '雅虎财经': 'https://finance.yahoo.com/news/rss',
    'CNBC': 'https://search.cnbc.com/rs/search/combinedcms/view.xml?id=10000664',
    '联合早报': 'https://www.zaobao.com/realtime/china/rss'
}

# 配置 Gemini API (需在 GitHub Secrets 中配置 GEMINI_API_KEY)
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')

def summarize_with_ai(text):
    if not api_key:
        return text[:150] + "..." # 如果没有配置 API，则截取前 150 字
    try:
        prompt = f"请作为资深新闻编辑，将以下新闻内容总结为300字左右的深度提炼，客观简练：\n{text}"
        response = model.generate_content(prompt)
        return response.text.replace('\n', '')
    except Exception as e:
        return text[:150] + "..."

all_news = []

for source, url in FEEDS.items():
    print(f"正在抓取 {source}...")
    try:
        feed = feedparser.parse(url)
        # 强制 Top 10 数量控制
        for entry in feed.entries[:10]:
            raw_summary = entry.get('summary', '') or entry.get('description', '')
            ai_summary = summarize_with_ai(raw_summary)
            
            all_news.append({
                'source': source,
                'title': entry.get('title', ''),
                'link': entry.get('link', ''),
                'summary': ai_summary
            })
    except Exception as e:
        print(f"{source} 抓取失败: {e}")

# 生成前端所需的 JS 文件
with open('news_data.js', 'w', encoding='utf-8') as f:
    f.write(f"const newsData = {json.dumps(all_news, ensure_ascii=False, indent=4)};")

print("所有新闻更新完成并打包为 JS！")