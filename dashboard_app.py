import dash
from dash import dcc, html # Dash Core Components and HTML components
from dash.dependencies import Input, Output, State # For callbacks
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px # For later use with charts
from collections import Counter # For genre counting

# Global variable for movie data
df_movies = None

def load_movie_data(xls_path="豆瓣电影Top250.xls"):
    """
    Loads movie data from the specified Excel file into the global df_movies DataFrame.
    Includes error handling for file not found and other potential read errors.
    """
    global df_movies
    try:
        df_movies = pd.read_excel(xls_path)
        print(f"Data loaded successfully from {xls_path}.")
        # Basic data cleaning (example: ensure '年份' (Year) is numeric if it exists)
        # This can be expanded based on specific column needs for charts
        if '年份' in df_movies.columns:
            df_movies['年份'] = pd.to_numeric(df_movies['年份'], errors='coerce')
        if '评分' in df_movies.columns:
            df_movies['评分'] = pd.to_numeric(df_movies['评分'], errors='coerce')
        # Add more cleaning as identified for other columns like '国家', '类型'

    except FileNotFoundError:
        print(f"Error: The file {xls_path} was not found.")
        df_movies = pd.DataFrame() # Initialize with an empty DataFrame on error
    except Exception as e:
        print(f"An error occurred while reading the file {xls_path}: {e}")
        df_movies = pd.DataFrame() # Initialize with an empty DataFrame on error

# Load data when the script is initialized
load_movie_data()

# Chart generation functions
def create_movies_by_year_bar_chart(df, year_range=None): # Added year_range parameter
    if df is None or df.empty:
        return None
    if '年份' not in df.columns:
        print("Error: '年份' column not found for create_movies_by_year_bar_chart.")
        return None

    df_cleaned = df.dropna(subset=['年份']).copy() # Use .copy() to avoid SettingWithCopyWarning
    df_cleaned['年份'] = df_cleaned['年份'].astype(int) # Convert to int early

    if year_range and len(year_range) == 2:
        min_year, max_year = year_range
        df_to_process = df_cleaned[
            (df_cleaned['年份'] >= int(min_year)) &
            (df_cleaned['年份'] <= int(max_year))
        ]
    else:
        df_to_process = df_cleaned

    if df_to_process.empty: # Check if filtered df is empty
        return px.bar(title=f"在年份范围 {year_range[0]}-{year_range[1]} 内无电影数据" if year_range else "无电影数据")


    year_counts = df_to_process['年份'].value_counts().sort_index()

    if year_counts.empty: # Should be redundant if df_to_process check is done, but good for safety
        return px.bar(title="处理后无年份数据")


    fig = px.bar(
        year_counts,
        x=year_counts.index,
        y=year_counts.values,
        labels={'x': '年份', 'y': '电影数量'},
        title='豆瓣 Top250 电影年份分布'
    )
    fig.update_layout(
        xaxis_title="年份",
        yaxis_title="电影数量",
        # xaxis_tickangle=-45 # Optional: if years are too crowded
    )
    return fig

def create_movies_by_country_pie_chart(df, top_n=10):
    if df is None or df.empty:
        return None
    if '国家' not in df.columns:
        print("错误: '国家' 列不存在于 DataFrame 中。")
        return None

    # Process '国家' column, taking the first country if multiple are listed
    df_copy = df.copy()
    # Ensure '国家' column is string type before splitting
    df_copy['主要国家'] = df_copy['国家'].astype(str).apply(lambda x: x.split('/')[0].strip())

    # Filter out empty strings or "nan" strings that might result from astype(str) if original data was NaN
    df_copy = df_copy[df_copy['主要国家'].str.lower() != 'nan']
    df_copy = df_copy[df_copy['主要国家'] != '']

    country_counts = df_copy['主要国家'].value_counts()

    if country_counts.empty:
        return None

    # Take Top N countries, group others into "其他"
    if len(country_counts) > top_n:
        top_countries = country_counts.nlargest(top_n)
        other_count = country_counts[~country_counts.index.isin(top_countries.index)].sum()
        if other_count > 0:
            # top_countries['其他'] = other_count # This might cause issues if '其他' is already an index
            # A safer way to add '其他'
            other_series = pd.Series([other_count], index=['其他'])
            country_counts_final = pd.concat([top_countries, other_series])

        else:
            country_counts_final = top_countries
    else:
        country_counts_final = country_counts

    fig = px.pie(
        country_counts_final,
        names=country_counts_final.index,
        values=country_counts_final.values,
        title=f'豆瓣 Top250 电影主要制片国家/地区分布 (Top {top_n})'
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    # fig.update_layout(legend_title_text='国家/地区')
    return fig

def create_movies_by_genre_hbar_chart(df):
    if df is None or df.empty:
        return None
    if '类型' not in df.columns:
        print("错误: '类型' 列不存在于 DataFrame 中。")
        return None

    # Process '类型' column
    df_copy = df.copy()
    df_copy['类型'] = df_copy['类型'].astype(str).apply(lambda x: x.strip())

    # Filter out empty or "nan" genre strings
    df_copy = df_copy[df_copy['类型'].str.lower().ne("nan") & df_copy['类型'].str.strip().ne("")]

    if df_copy.empty:
        print("Warning: DataFrame became empty after filtering '类型' for 'nan' or empty strings.")
        return None

    genre_list = []
    for genres_str in df_copy['类型']:
        # Split by '/' first, then by space for each part, and strip
        cleaned_genres = [genre.strip() for part in genres_str.split('/') for genre in part.split(' ') if genre.strip()]
        genre_list.extend(cleaned_genres)

    if not genre_list:
        print("Warning: No genres found after processing the '类型' column.")
        return None

    genre_counts = Counter(genre_list)

    genre_counts_df = pd.DataFrame(
        list(genre_counts.items()), columns=['类型', '数量']
    ).sort_values(by='数量', ascending=True)

    if genre_counts_df.empty:
        print("Warning: Genre counts DataFrame is empty.")
        return None

    fig = px.bar(
        genre_counts_df,
        x='数量',
        y='类型',
        orientation='h',
        title='豆瓣 Top250 电影类型统计',
        labels={'数量': '电影数量', '类型': '电影类型'},
        height=max(400, len(genre_counts_df) * 20) # Dynamically adjust height
    )
    fig.update_layout(
        yaxis_title="电影类型",
        xaxis_title="电影数量",
        margin=dict(l=100) # Adjust left margin to prevent labels from being cut off
    )
    return fig

def create_avg_rating_by_year_line_chart(df):
    if df is None or df.empty:
        return None
    required_cols = ['年份', '评分']
    for col in required_cols:
        if col not in df.columns:
            print(f"错误: '{col}' 列不存在于 DataFrame 中。")
            return None

    df_copy = df.copy()

    # Ensure '年份' and '评分' are not NaN after potential coercion in load_movie_data
    df_copy = df_copy.dropna(subset=required_cols)

    if df_copy.empty:
        print("警告: 清洗后没有有效的年份或评分数据用于生成年度平均评分图表。")
        return None

    # Convert '年份' to integer for cleaner display and '评分' to float
    try:
        df_copy['年份'] = df_copy['年份'].astype(int)
        df_copy['评分'] = df_copy['评分'].astype(float)
    except ValueError as e:
        print(f"Error converting '年份' or '评分' to numeric types: {e}")
        return None

    avg_rating_by_year = df_copy.groupby('年份')['评分'].mean().sort_index()

    if avg_rating_by_year.empty:
        print("警告: 年度平均评分数据为空。")
        return None

    fig = px.line(
        avg_rating_by_year,
        x=avg_rating_by_year.index,
        y=avg_rating_by_year.values,
        title='豆瓣 Top250 电影年度平均评分趋势',
        labels={'x': '年份', 'y': '平均评分'},
        markers=True
    )
    fig.update_layout(
        xaxis_title="年份",
        yaxis_title="平均评分",
    )

    # Improve X-axis tick display
    # If years are numerous, default tick mode is fine. If few, show all.
    if len(avg_rating_by_year.index) < 20: # Heuristic for "few" years
        fig.update_xaxes(type='category') # Treat years as categories to show all ticks
    else: # For many years, ensure ticks are reasonable (e.g. every 5 years if range is large)
        # This part may need further refinement based on actual data range
        # For now, relying on Plotly's auto-ticks for larger year ranges.
        pass

    return fig

def create_rating_distribution_histogram(df):
    if df is None or df.empty:
        return None
    if '评分' not in df.columns:
        print("错误: '评分' 列不存在于 DataFrame 中。")
        return None

    df_copy = df.copy()

    # Clean '评分' column from NaN values
    df_copy = df_copy.dropna(subset=['评分'])

    if df_copy.empty or df_copy['评分'].isnull().all():
        print("警告: 清洗后没有有效的评分数据用于生成评分分布图表。")
        return None

    try:
        df_copy['评分'] = df_copy['评分'].astype(float)
    except ValueError:
        print("错误: '评分' 列无法转换为浮点数。")
        return None

    fig = px.histogram(
        df_copy,
        x='评分',
        title='豆瓣 Top250 电影评分分布',
        labels={'评分': '电影评分', 'count': '电影数量'},
        nbins=20,
        # histnorm='percent', # Optional: Display Y-axis as percentage
        # marginal="box",     # Optional: Add box plot at the top
    )
    fig.update_layout(
        xaxis_title="电影评分",
        yaxis_title="电影数量",
        bargap=0.1, # Gap between bars
    )
    # fig.update_xaxes(tick0=df_copy['评分'].min(), dtick=0.5) # Optional: Finer control over X-axis ticks
    return fig

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True) # suppress_callback_exceptions for dynamic layout
server = app.server # Expose Flask server for potential WSGI deployment

# Styles definition
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

# Sidebar layout
sidebar = html.Div(
    [
        html.H2("电影分析", className="display-6"),
        html.Hr(),
        html.P(
            "选择一个维度进行查看:", className="lead"
        ),
        dbc.Nav(
            [
                dbc.NavLink("年度电影数量", href="/page-1", active="exact", className="ms-2 mb-1"),
                dbc.NavLink("国家/地区分布", href="/page-2", active="exact", className="ms-2 mb-1"),
                dbc.NavLink("类型统计", href="/page-3", active="exact", className="ms-2 mb-1"),
                dbc.NavLink("年度平均评分", href="/page-4", active="exact", className="ms-2 mb-1"),
                dbc.NavLink("评分分布", href="/page-5", active="exact", className="ms-2 mb-1"),
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=SIDEBAR_STYLE,
)

# Content area layout
content = html.Div(id="page-content", style=CONTENT_STYLE)

# App layout
app.layout = dbc.Container([
    dcc.Location(id="url"),
    sidebar,
    content
], fluid=True)

# Callback to update page content based on URL
@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if df_movies is None or df_movies.empty:
        return dbc.Alert("数据未能成功加载，请检查数据文件或应用配置。", color="danger", className="m-3")

    if pathname == "/" or pathname == "/page-1":
        if '年份' not in df_movies.columns:
             return dbc.Alert("错误: 数据中缺少 '年份' 列，无法生成图表。", color="danger")

        valid_years = pd.to_numeric(df_movies['年份'], errors='coerce').dropna().astype(int)
        if valid_years.empty:
            min_year, max_year = 2000, 2020 # Fallback
            initial_slider_value = [min_year, max_year]
            marks_slider = {str(y): str(y) for y in range(min_year, max_year + 1, 5)}
        else:
            min_year = int(valid_years.min())
            max_year = int(valid_years.max())
            initial_slider_value = [min_year, max_year]
            # Adjust mark step based on range, e.g. if range is small, step is 1
            year_span = max_year - min_year
            mark_step = 1 if year_span <= 10 else 5 if year_span <= 50 else 10
            marks_slider = {str(year): str(year) for year in range(min_year, max_year + 1, mark_step)}


        page_1_layout = html.Div([
            dbc.Card(dbc.CardBody([
                html.H4("年度电影数量统计", className="card-title"),
                dbc.Row([
                    dbc.Col(html.Label("选择年份范围:"), width='auto', className="me-2 align-self-center"),
                    dbc.Col(
                        dcc.RangeSlider(
                            id='year-range-slider',
                            min=min_year,
                            max=max_year,
                            step=1,
                            value=initial_slider_value,
                            marks=marks_slider,
                            tooltip={"placement": "bottom", "always_visible": True}
                        ),
                        width=8,
                        className="mt-1" # margin top for slider
                    )
                ], align="center", className="mb-3"),
                dcc.Graph(id='movies-by-year-chart')
            ])),
        ])
        return page_1_layout

    elif pathname == "/page-2":
        if '国家' not in df_movies.columns:
            return dbc.Alert("错误: 数据中缺少 '国家' 列，无法生成图表。", color="danger")
        fig_country = create_movies_by_country_pie_chart(df_movies, top_n=10)
        if fig_country:
            return dbc.Card(dbc.CardBody([
                        html.H4("国家/地区电影数量分布 (Top 10)", className="card-title"),
                        dcc.Graph(figure=fig_country)
                    ]))
        else:
            return dbc.Alert("无法生成国家/地区电影数量图表。可能是数据中没有有效的国家信息。", color="warning")
    elif pathname == "/page-3":
        if '类型' not in df_movies.columns:
            return dbc.Alert("错误: 数据中缺少 '类型' 列，无法生成图表。", color="danger")
        fig_genre = create_movies_by_genre_hbar_chart(df_movies)
        if fig_genre:
            return dbc.Card(dbc.CardBody([
                        html.H4("电影类型统计", className="card-title"),
                        dcc.Graph(figure=fig_genre)
                    ]))
        else:
            return dbc.Alert("无法生成类型电影数量图表。可能是'类型'数据为空或格式不正确。", color="warning")
    elif pathname == "/page-4":
        required_cols_check = ['年份', '评分']
        for col_check in required_cols_check:
            if col_check not in df_movies.columns:
                return dbc.Alert(f"错误: 数据中缺少 '{col_check}' 列，无法生成图表。", color="danger")

        fig_avg_rating = create_avg_rating_by_year_line_chart(df_movies)
        if fig_avg_rating:
            return dbc.Card(dbc.CardBody([
                        html.H4("年度平均评分趋势", className="card-title"),
                        dcc.Graph(figure=fig_avg_rating)
                    ]))
        else:
            return dbc.Alert("无法生成年度平均评分趋势图表。可能是数据不满足要求或清洗后无有效数据。", color="warning")
    elif pathname == "/page-5":
        if '评分' not in df_movies.columns:
            return dbc.Alert("错误: 数据中缺少 '评分' 列，无法生成图表。", color="danger")

        fig_rating_dist = create_rating_distribution_histogram(df_movies)
        if fig_rating_dist:
            return dbc.Card(dbc.CardBody([
                        html.H4("电影评分分布", className="card-title"),
                        dcc.Graph(figure=fig_rating_dist)
                    ]))
        else:
            return dbc.Alert("无法生成评分分布图表。可能是'评分'数据不满足要求或清洗后无有效数据。", color="warning")
    # Removed explicit handling for pathname == "/" as it's covered by the first condition now

    return dbc.Container(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"The pathname {pathname} was not recognised..."),
        ],
        className="py-3",
    )

# Callback for updating the movies_by_year_chart based on RangeSlider
@app.callback(
    Output('movies-by-year-chart', 'figure'),
    [Input('year-range-slider', 'value')]
)
def update_movies_by_year_chart(year_range):
    if df_movies is None or df_movies.empty or '年份' not in df_movies.columns:
        return px.bar(title="数据加载中或年份数据不可用...", labels={'x':'年份', 'y':'电影数量'})

    fig = create_movies_by_year_bar_chart(df_movies, year_range)
    if fig:
        return fig
    else:
        return px.bar(title=f"在年份范围 {year_range[0]}-{year_range[1]} 内无数据", labels={'x':'年份', 'y':'电影数量'})

# Main run block
if __name__ == '__main__':
    # Re-load data in case the script is run directly and was imported elsewhere before
    # Though for a simple script like this, the initial load should be sufficient.
    if df_movies is None or df_movies.empty:
        print("Attempting to reload data for __main__ execution...")
        load_movie_data()
        if df_movies.empty:
            print("Failed to load data. Dashboard may not work correctly.")
            # Optionally, app.layout could be updated here to show a permanent error message.
    app.run_server(debug=True)
