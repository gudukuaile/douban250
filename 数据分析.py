# -*- coding: utf-8 -*-
"""
豆瓣电影Top250数据分析脚本
功能：对豆瓣电影Top250数据进行多维度分析，包括评分分布、年份趋势、国家分布等
作者：AI助手
日期：2024
"""

# 导入必要的库
import pandas as pd  # 用于数据处理和分析，提供DataFrame等数据结构
import matplotlib.pyplot as plt  # 用于数据可视化，创建各种图表
import seaborn as sns  # 用于统计数据可视化，提供更美观的统计图表
from collections import Counter  # 用于统计词频，快速计算元素出现次数
from wordcloud import WordCloud
import numpy as np
import matplotlib.cm as cm

# 设置matplotlib的中文字体支持，解决中文显示问题
plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体为黑体，确保中文正常显示
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题，防止负号显示为方块

# 读取Excel文件
file_path = "豆瓣电影Top250.xls"  # 数据文件路径
df = pd.read_excel(file_path)  # 使用pandas读取Excel文件到DataFrame

# 数据清洗和预处理
# 将"评分"列转换为浮点数类型，便于后续数值计算
df["评分"] = df["评分"].astype(float)

# 提取"评价人数数值"字段中的数字部分
# 处理步骤：
# 1. 将数据转为字符串
# 2. 使用正则表达式提取数字（去除所有非数字字符）
# 3. 将结果转换为整数类型
df["评价人数数值"] = df["评价人数"].astype(str).str.replace(r'\D+', '', regex=True).astype(int)

# 提取"年份"字段
# 使用正则表达式提取4位数字年份，并转换为整数类型
df["年份"] = df["年份"].astype(str).str.extract(r'(\d{4})').astype(int)

# 提取"国家"字段，去掉前后空格，确保数据整洁
df["国家"] = df["国家"].str.strip()

# 提取"类型"字段，将字符串按空格分割成列表，用于后续词频统计
df["类型列表"] = df["类型"].str.split()

# 提取"导演"的中文名（假设中文名是第一个词）
df["导演中文名"] = df["导演"].str.split().str[0]

# 打印数据加载完成的信息和示例数据
print("✅ 数据加载完成，前几行示例：")
print(df.head())

# ——————————————————————
# 分析一：评分分布直方图
# 目的：了解电影评分的整体分布情况
# 使用seaborn绘制评分分布的直方图，并添加核密度估计曲线
# ——————————————————————
plt.figure(figsize=(10, 6))  # 设置图表大小
sns.histplot(df["评分"], bins=10, kde=True, color="skyblue")  # 绘制直方图和密度曲线
plt.title("豆瓣电影 Top250 评分分布直方图")
plt.xlabel("评分")
plt.ylabel("电影数量")
plt.grid(True)  # 添加网格线
plt.show()

# ——————————————————————
# 分析二：年份趋势图
# 目的：了解电影在不同年份的分布情况
# 统计各年份的电影数量，并绘制柱状图
# ——————————————————————
year_counts = df["年份"].value_counts().sort_index()  # 统计各年份电影数量并排序
plt.figure(figsize=(12, 6))
year_counts.plot(kind='bar')  # 绘制柱状图
plt.title("各年份电影数量分布")
plt.xlabel("年份")
plt.ylabel("数量")
plt.xticks(rotation=45)  # 旋转x轴标签，防止重叠
plt.tight_layout()  # 自动调整布局
plt.show()

# ——————————————————————
# 分析三：国家分布（Top5）饼图
# 目的：了解电影的国家/地区分布情况，统一处理中国相关地区
# ——————————————————————
# 处理国家数据
def process_country(country_str):
    if not isinstance(country_str, str):
        return []
    
    # 定义中国相关地区的映射
    china_related = ['中国', '香港', '台湾', '大陆']
    
    # 分割并处理每个国家
    countries = []
    for country in country_str.split():
        country = country.strip()
        # 如果包含中国相关地区，统一标记为中国
        if any(region in country for region in china_related):
            country = '中国'
        if country and country not in countries:  # 确保不重复添加
            countries.append(country)
    return countries

# 展开多国家数据
all_countries = []
for countries in df['国家'].apply(process_country):
    all_countries.extend(countries)

# 统计国家出现次数
country_counts = pd.Series(all_countries).value_counts().head(5)

# 绘制饼图
plt.figure(figsize=(10, 8))
plt.pie(country_counts, labels=country_counts.index, autopct='%1.1f%%', 
        colors=sns.color_palette('pastel'), startangle=90)
plt.title('电影国家/地区分布（Top5）\n注：多国合拍电影会被重复计算')
plt.axis('equal')  # 确保饼图是圆的
plt.show()

# 打印详细数据
print("\n国家/地区分布详细数据：")
print(country_counts)

# ——————————————————————
# 分析四：评分区间分布
# 目的：了解电影评分的区间分布情况
# ——————————————————————
# 创建评分区间
bins = [0, 8.5, 9.0, 9.5, 10.0]
labels = ['8.0-8.5', '8.5-9.0', '9.0-9.5', '9.5-10.0']
df['评分区间'] = pd.cut(df['评分'], bins=bins, labels=labels)

# 统计各区间电影数量
score_dist = df['评分区间'].value_counts().sort_index()

# 绘制条形图
plt.figure(figsize=(10, 6))
score_dist.plot(kind='bar', color='lightblue')
plt.title('电影评分区间分布')
plt.xlabel('评分区间')
plt.ylabel('电影数量')
plt.xticks(rotation=45)
plt.grid(True, axis='y')
plt.tight_layout()
plt.show()

# ——————————————————————
# 分析五：电影类型统计（词云图）
# 目的：了解电影类型的分布情况
# ——————————————————————
# 将所有电影类型展开成一个列表
all_genres = [genre for genres in df["类型列表"] for genre in genres]
# 使用Counter统计词频
genre_counter = Counter(all_genres)

# 创建词云图
plt.figure(figsize=(12, 8))
# 生成词云
wordcloud = WordCloud(
    font_path='simhei.ttf',  # 使用黑体字体
    width=1000,
    height=800,
    background_color='white',
    max_words=100,
    max_font_size=150,
    random_state=42
)

# 生成词云
wordcloud.generate_from_frequencies(genre_counter)

# 显示词云图
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis('off')  # 关闭坐标轴
plt.title('电影类型词云图', fontsize=20, pad=20)
plt.tight_layout()
plt.show()

# 打印详细数据
print("\n电影类型出现次数（Top10）：")
print(pd.Series(genre_counter).sort_values(ascending=False).head(10))

# ——————————————————————
# 分析六：导演作品数量排行（Top10）
# 目的：了解高产导演的分布情况
# 统计导演的作品数量，展示前10名
# ——————————————————————
director_counts = df["导演中文名"].value_counts().head(10)  # 获取作品数量前10的导演
plt.figure(figsize=(10, 6))
director_counts.plot(kind='barh', color='gold')  # 绘制水平柱状图
plt.title("导演作品数量排行（Top10）")
plt.xlabel("数量")
plt.ylabel("导演")
plt.gca().invert_yaxis()  # 反转y轴，使作品数量最多的显示在顶部
plt.show()

# ——————————————————————
# 分析七：评分 vs 评价人数 散点图
# 目的：分析评分与评价人数之间的关系
# 使用散点图展示两个变量之间的关系
# ——————————————————————
plt.figure(figsize=(10, 6))
sns.scatterplot(x="评分", y="评价人数数值", data=df, alpha=0.7)  # 绘制散点图，设置透明度
plt.title("评分 vs 评价人数")
plt.xlabel("评分")
plt.ylabel("评价人数")
plt.grid(True)  # 添加网格线
plt.show()

# ——————————————————————
# 分析八：电影类型玫瑰图
# 目的：使用玫瑰图展示电影类型的分布情况
# ——————————————————————
# 获取前15个最常见的电影类型
top_genres = dict(genre_counter.most_common(15))

# 创建玫瑰图
plt.figure(figsize=(12, 8))
ax = plt.subplot(111, projection='polar')  # 创建极坐标图

# 准备数据
angles = np.linspace(0, 2*np.pi, len(top_genres), endpoint=False)
values = list(top_genres.values())
labels = list(top_genres.keys())

# 闭合数据
angles = np.concatenate((angles, [angles[0]]))
values = np.concatenate((values, [values[0]]))

# 绘制玫瑰图
ax.plot(angles, values, 'o-', linewidth=2)
ax.fill(angles, values, alpha=0.25)

# 设置标签
ax.set_xticks(angles[:-1])
ax.set_xticklabels(labels, fontsize=10)

# 设置标题
plt.title('电影类型分布玫瑰图', pad=20, fontsize=15)

# 调整布局
plt.tight_layout()
plt.show()

print("📊 分析完成！")

# ——————————————————————
# 分析九：电影类型极坐标条形图（玫瑰图）
# 目的：用极坐标条形图展示电影类型分布
# ——————————————————————

# 统计所有电影类型出现次数，取前20个
genre_counts = pd.Series(all_genres).value_counts().head(20)
labels = genre_counts.index.tolist()
values = genre_counts.values

# 极坐标参数
N = len(labels)
theta = np.linspace(0.0, 2 * np.pi, N, endpoint=False)
radii = values
width = 2 * np.pi / N

# 颜色映射
colors = cm.tab20(np.arange(N))

plt.figure(figsize=(12, 8))
ax = plt.subplot(111, polar=True)
bars = ax.bar(theta, radii, width=width, bottom=0.0, color=colors, alpha=0.8, edgecolor='black')

# 设置每个扇形的标签
for i, (bar, label) in enumerate(zip(bars, labels)):
    angle = np.degrees(theta[i])
    ha = 'left' if 90 < angle < 270 else 'right'
    ax.text(theta[i], radii[i] + max(radii)*0.05, label, ha=ha, va='center', fontsize=10, color=colors[i])

# 去掉极坐标的刻度
ax.set_xticks([])
ax.set_yticks([])

plt.title('电影类型分布极坐标条形图（玫瑰图）', fontsize=16, pad=20)
plt.tight_layout()
plt.show()