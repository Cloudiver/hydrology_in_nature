import re
import requests
from bs4 import BeautifulSoup

import re

def remove_html_tags_except_sub_sup(text):
    # 正则表达式：匹配除了 <sub> 和 <sup> 之外的所有 HTML 标签
    clean_text = re.sub(r'<(?!\/?(sub|sup)\b)[^>]+>', '', text)
    return clean_text


def convert_to_full_image(url):
    """将图片URL转换为完整尺寸版本"""
    if not url:
        return url
    parts = url.split('/')
    # media.springernature.com 后面的参数是我们要替换的
    for i, part in enumerate(parts):
        if 'springernature.com' in part and i + 1 < len(parts):
            parts[i + 1] = 'full'
            break
    return '/'.join(parts)


def get_description(url, headers):
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    description = soup.select('#Abs1-content p')

    authors = soup.select('ul[data-test="authors-list"] li a[data-test="author-name"]')
    author_names = [author.get_text() for author in authors]

    # bug: 部分情况下可能无摘要, 如: https://doi.org/10.1038/s41586-024-08358-0
    # 已解决
    if len(description) == 0:
        description = 'This article has no abstract.'
        return description, "; ".join(author_names)
    else:
        description = remove_html_tags_except_sub_sup(description[0])
        return description, "; ".join(author_names)


def get_affiliation(url, headers):
    """获取作者单位"""
    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        affiliations = soup.select('.c-article-author-affiliation__address')
        affiliations = [aff.get_text().strip() for aff in affiliations if aff.get_text().strip()]
        return '; '.join(affiliations)
    except Exception as e:
        print(f"获取作者单位时发生错误: {e}")
        return ""

def get_article_titles(base_url, need_journal, last_first_article=None):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": base_url,
            "Content-Type": "text/html; charset=UTF-8"
        }
        
        response = requests.get(base_url, headers=headers)
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        elements = soup.select('.app-article-list-row li a')
        elements2 = soup.select('.app-article-list-row li time')
        elements3 = soup.select('.app-article-list-row li [data-test="journal-title-and-link"]')
        img_elements = soup.select('.c-card__image picture img')
        
        papers = []
        for index, title in enumerate(elements):
            full_text = title.get_text().strip()
            href = 'https://www.nature.com' + title['href']
            article_date = elements2[index]['datetime']
            journal = elements3[index].get_text().strip()
            img_src = convert_to_full_image(img_elements[index]['src'])

            if last_first_article and href == last_first_article:
                # last_article_found = True
                break

            if journal in need_journal:
                # 获取摘要, 作者信息
                description, author_names = get_description(href, headers)

                print(f"{full_text}")
                print(f"   作者: {author_names}")
                print(f"   链接: {href}")
                print(f"   日期: {article_date}")
                print(f"   期刊: {journal}")
                print(f"   图片: {img_src}\n")

                # 只需要特定期刊
                papers.append([full_text, author_names, href, article_date, description, journal, img_src])
            
            if papers and len(papers) == 10:
                return papers, papers[0][1]
            
        return papers, papers[0][1] if papers else None

    except Exception as e:
        print(f"发生错误: {e}")
        return []
    

def get_last_line_third_element(filename):
    """
    读取文件最后一行并返回按逗号分割后的第三个元素
    """
    try:
        with open(filename, 'rb') as f:
            off = -50
            while True:
                f.seek(off, 2) #seek(off, 2)表示文件指针：从文件末尾(2)开始向前50个字符(-50)
                lines = f.readlines() #读取文件指针范围内所有行
                if len(lines)>=2: #判断是否最后至少有两行，这样保证了最后一行是完整的
                    last_line = lines[-1] #取最后一行
                    break
                off *= 2

            # 读取最后一行并分割
            last_line = last_line.decode('utf-8').strip()
            elements = last_line.split(',')
            
            return elements[1] if len(elements) > 1 else None
            
    except FileNotFoundError:
        return None


def main():
    with open('subjects.txt', encoding='utf-8') as f:
        subjects = [subject.strip() for subject in f.readlines()]
        if len(subjects) == 1:
            url = f'https://www.nature.com/search?article_type=research%2C+reviews&subject={subjects[0]}&order=date_desc&page=1'
        elif len(subjects) > 1:
            subjects = ',%20'.join(subjects)
            url = f'https://www.nature.com/search?article_type=research%2C+reviews&subject={subjects}&order=date_desc&page=1'
        else:
            print('subjects不能为空')
            return

    with open('journal list.txt') as f:
        journals = [journal.strip() for journal in f.readlines()]   
        
    last_first_article = get_last_line_third_element('last_article.txt')
    # print(last_first_article)
        
    papers, current_first_article = get_article_titles(url, journals, last_first_article)

    if not papers:
        # print("今天没有新文章")
        return

    if current_first_article:
        with open('last_article.txt', 'a', encoding='utf-8') as f:
            for paper in papers[::-1]:
                f.write(paper[0] + ',')   # 写入最新文章标题
                f.write(paper[2] + ',')   # 写入最新文章链接
                f.write(paper[3] + ',')   # 写入最新文章日期
                f.write(paper[4] + ',')   # 写入最新文章摘要
                f.write(paper[5] + '\n')   # 写入期刊
    return papers


if __name__ == "__main__":
    main()