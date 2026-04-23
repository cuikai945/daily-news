import feedparser
import json
import os
import time
import httpx
from zhipuai import ZhipuAI

# 🌟 1. 从云端“保险箱”（环境变量）安全读取 API Key
ZHIPU_API_KEY = os.environ.get("ZHIPU_API_KEY")
if not ZHIPU_API_KEY:
    print("🚨 致命错误: 未获取到 ZHIPU_API_KEY！请检查 GitHub Secrets 是否配置正确。")
    exit(1)
client = ZhipuAI(api_key=ZHIPU_API_KEY)

# 🌟 2. 读取关键词备忘录
watch_keywords = ""
keyword_file = "keywords.txt"
if os.path.exists(keyword_file):
    with open(keyword_file, "r", encoding="utf-8") as f:
        watch_keywords = f.read().strip()
    print(f"📖 已读取今日关注关键词: {watch_keywords}")
else:
    print("📖 未发现 keywords.txt，当前无特别关注关键词。")

# 🌟 3. 融合中外 8 大顶尖权威新闻源 (替换联合早报为人民日报)
rss_urls = [
    {"source": "FT中文网", "url": "http://www.ftchinese.com/rss/news"},
    {"source": "BBC", "url": "http://feeds.bbci.co.uk/news/world/rss.xml"},
    {"source": "纽约时报", "url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"}, 
    {"source": "华尔街日报", "url": "https://feeds.a.dj.com/rss/RSSWorldNews.xml"}, 
    {"source": "36氪", "url": "https://36kr.com/feed"},
    {"source": "雅虎财经", "url": "https://finance.yahoo.com/news/rss"}, 
    {"source": "CNBC", "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664"}, 
    {"source": "人民日报", "url": "http://www.people.com.cn/rss/world.xml"}
]

final_news_data = []
news_id = 1

print("\n🚀 深度情报版 AI 自动读报机器人开始运行...")
print("-----------------------------------")

# 完美伪装成真实的 Chrome 浏览器
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

for feed_info in rss_urls:
    print(f"\n📡 正在前往 {feed_info['source']} 抓取新闻...")
    try:
        # 使用 httpx 进行带面具的强力穿透
        response = httpx.get(feed_info['url'], headers=headers, timeout=20.0, follow_redirects=True)
        if response.status_code != 200:
            print(f"  [失败] 服务器拒绝访问，状态码: {response.status_code}")
            continue
        feed = feedparser.parse(response.content)
    except Exception as e:
        print(f"  [失败] 无法连接到 {feed_info['source']}, 错误: {e}")
        continue

    success_count = 0
    
    # 扩大候选池，强制必须凑够 10 条
    for entry in feed.entries[:25]:
        if success_count >= 10:
            print(f"  🎯 {feed_info['source']} 已成功抓取 10 条，前往下一个平台。")
            break
            
        title = entry.title
        link = entry.link
        raw_summary = entry.description if hasattr(entry, 'description') else "无"
        
        keyword_instruction = ""
        if watch_keywords:
            keyword_instruction = f"""
            非常重要：用户当前特别关注以下关键词：【{watch_keywords}】。
            如果这篇新闻的内容与上述任何一个关键词高度相关，请务必将 isImportant 设为 true，并在 keyword 字段填入命中的关键词（如果没有命中，isImportant 设为 false，keyword 留空）。
            """

        # 强制要求 300-500 字深度总结
        prompt_text = f"""
        你是一个专业的新闻主编和高级情报分析师。请深度阅读以下新闻情报：
        标题: {title}
        摘要: {raw_summary}
        
        请完成以下任务：
        1. 如果是外文，请精准翻译成流畅的中文。
        2. 用 300-500 字极其详细地总结这篇新闻的核心事件、背景细节和深远影响（客观冷静）。请保证信息量极高，让读者完全无需阅读原文即可掌握所有重要细节。
        3. 判断所属地区 (仅限：中国、美国、欧洲、全球、其他)。
        4. 判断所属种类 (仅限：政治、宏观、财经、科技、政策)。
        {keyword_instruction}
        
        请严格以下面的 JSON 格式返回，不要有 Markdown 符号：
        {{"summary": "详细深度总结", "region": "地区", "type": "种类", "isImportant": false, "keyword": ""}}
        """

        retry_count = 0
        while retry_count < 3:
            try:
                response = client.chat.completions.create(
                    model="glm-4-flash",  
                    messages=[{"role": "user", "content": prompt_text}],
                    timeout=20 
                )
                
                ai_result_text = response.choices[0].message.content.strip()
                if ai_result_text.startswith("
