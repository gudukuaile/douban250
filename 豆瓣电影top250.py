# -*- coding: utf-8 -*-
import random
import requests
from bs4 import BeautifulSoup
import pandas as pd  # 替换xlwt为pandas
import time

# 设置请求头，模拟浏览器访问
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def fetch_html(url):
    """
    请求并获取网页内容
    参数:
        url: 要请求的网页URL
    返回:
        成功返回网页内容，失败返回None
    """
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()  # 检查请求是否成功
        response.encoding = 'utf-8'  # 设置编码为utf-8
        return response.text
    except Exception as e:
        print(f"❌ 请求失败：{url} | 错误：{e}")
        return None

def parse_page(html):
    """
    解析一页中的所有电影数据
    参数:
        html: 网页的HTML内容
    返回:
        包含该页所有电影信息的列表
    """
    soup = BeautifulSoup(html, "lxml")
    movies = []

    # 遍历页面中的每个电影条目
    for item in soup.select("div.item"):
        # 获取电影排名
        rank = item.select_one(".pic em").text.strip()
        # 获取电影详情页链接
        link = item.select_one("a")["href"]
        # 获取电影海报图片链接
        img_url = item.select_one("img")["src"]

        # 获取电影标题（中文名）
        title_zh = item.select_one(".title").text.strip()
        # 获取电影英文名（如果存在）
        title_en_tag = item.select_one(".title + .title")
        title_en = title_en_tag.text.strip() if title_en_tag else ""
        # 获取电影其他名称（如果存在）
        other_name_tag = item.select_one(".other")
        other_names = other_name_tag.text.strip().replace("\xa0/\xa0", "/") if other_name_tag else ""

        # 获取电影详细信息（导演、主演、年份、国家、类型）
        info_p = item.select_one(".bd p").get_text(strip=True, separator="###").split("###")
        if len(info_p) >= 2:
            # 处理导演和主演信息
            director_and_actor = info_p[0].strip().replace("\xa0\xa0\xa0", " ")
            year_country_genre = info_p[1].strip().split("/")

            # 分离导演和主演信息
            director_part = director_and_actor.split("主演:")[0].replace("导演:", "").strip()
            actor_part = director_and_actor.split("主演:")[-1].strip() if "主演:" in director_and_actor else ""

            # 提取年份、国家和类型信息
            year = year_country_genre[0].strip()
            country = year_country_genre[1].strip()
            genre = "/".join([g.strip() for g in year_country_genre[2:]])
        else:
            director_part = actor_part = year = country = genre = ""

        # 获取评分信息
        rating_tag = item.select_one(".rating_num")
        rating = rating_tag.text.strip() if rating_tag else ""

        # 获取评价人数
        judge_tag = item.select_one(".rating_num + span + span")  # 选择rating_num后的第二个span
        if judge_tag:
            judge_count = judge_tag.text.replace("人评价", "").strip()
        else:
            judge_count = ""

        # 获取电影简评语录
        quote_tag = item.select_one(".quote span")
        quote = quote_tag.text.strip() if quote_tag else ""

        # 将电影信息整理成字典
        movie_data = {
            "排名": rank,
            "中文名": title_zh,
            "英文名": title_en,
            "其他名称": other_names,
            "导演": director_part,
            "主演": actor_part,
            "年份": year,
            "国家": country,
            "类型": genre,
            "评分": rating,
            "评价人数": judge_count,
            "简评语录": quote,
            "详情链接": link,
            "图片链接": img_url
        }

        movies.append(movie_data)

    return movies

def save_to_excel(movies, filename="豆瓣电影Top250.xlsx"):
    """
    将电影数据保存到Excel文件中
    参数:
        movies: 电影数据列表
        filename: 保存的文件名，默认为"豆瓣电影Top250.xls"
    """
    # 将数据列表转换为DataFrame
    df = pd.DataFrame(movies)
    
    # 保存为Excel文件
    df.to_excel(filename, index=False, engine='openpyxl')
    print(f"✅ 数据已保存至文件：{filename}")

def main():
    """
    主函数：爬取豆瓣电影Top250的数据
    """
    baseurl = "https://movie.douban.com/top250?start="
    all_movies = []

    # 爬取10页数据（每页25部电影）
    for i in range(0, 10):
        url = baseurl + str(i * 25)
        print(f"🌐 正在爬取第 {i+1} 页：{url}")
        html = fetch_html(url)
        if html:
            movies = parse_page(html)
            all_movies.extend(movies)
        # 随机延时1-2秒，避免请求过于频繁
        sleep_time = random.uniform(1, 2)
        time.sleep(sleep_time)

    # 保存数据到Excel文件
    save_to_excel(all_movies)

if __name__ == "__main__":
    main()