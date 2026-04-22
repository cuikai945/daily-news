import feedparser
import json
import os
import requests
from zhipuai import ZhipuAI

# 设置 8 大平台源 (包含联合早报)
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

# 配置智谱 AI (需在 GitHub Secrets 中配置 ZHIPU_API_KEY)
api_key = os.environ.get("ZHIPU_API_KEY")
client = ZhipuAI(api_key=api_key) if api_key else None

def summarize_with_ai(text):
    if not client:
        return text[:150] + "..." # 如果没有配置 API，则截取前 150 字
    try:
        response = client.chat.completions.create(
            model="glm-4",  # 调用智谱最新的 GLM-4 模型
            messages=[
                {"role": "system", "content": "你是一个资深政经新闻编辑。"},
                {"role": "user", "content": f"请将以下新闻内容总结为300字左右的深度提炼，客观、简练、直击要害：\n{text}"}
            ],
        )
        return response.choices[0].message.content.replace('\n', '')
    except Exception as e:
        print(f"AI 总结失败: {e}")
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
