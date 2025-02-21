from feedgen.feed import FeedGenerator
import nature_article as nature_rss
from datetime import datetime
import pytz
from pygtrans import Translate


def create_rss_feed(articles):
    GT = Translate()
    title_trans =GT.translate([article[0] for article in articles], source="auto", target="zh-CN")   # 同时翻译文章标题
    abstract_trans = GT.translate([article[4] for article in articles], source="auto", target="zh-CN")   # 同时翻译文章摘要

    
    fg = FeedGenerator()
    for index, article in enumerate(articles):
        fe = fg.add_entry()
        fe.title(article[-2] + " | " + title_trans[index].translatedText)
        fe.link(href=article[2])
        fe.description('<b>标题: </b>' + article[0] + '<br/><br/><b>作者:</b> ' + article[1] + '<br/><br/><b>摘要（谷歌翻译）</b><br/>' + abstract_trans[index].translatedText + '<br/><br/><b>英文摘要</b><br/>' + article[4] + '<br/><br/><img src="' + article[6] + '" />')
        # fe.image(article[6])
        pub_date = datetime.strptime(article[3], '%Y-%m-%d')
        pub_date = pytz.timezone('UTC').localize(pub_date)
        fe.pubDate(pub_date)
    fg.title('Nature Hydrology RSS Feed')
    fg.description('Nature Hydrology RSS Feed')
    fg.link(href='https://www.nature.com')
    fg.language('en')
    fg.rss_file('rss2025.xml')

if __name__ == "__main__":
    articles = nature_rss.main()
    if articles:
        create_rss_feed(articles)
    else:
        print("今天没有新文章")
