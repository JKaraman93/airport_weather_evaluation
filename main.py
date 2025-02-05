import pyodbc
import datetime
from metar_taf_parser.parser.parser import MetarParser
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import helpers as h
from collections import OrderedDict


# Database Connection
DB_PATH = r'C:\Users\Jim\Desktop\Archive\2023\2023_01\METEOImages_20230101\T20230101.MDB'
conn = pyodbc.connect(rf'Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={DB_PATH};')
cursor = conn.cursor()

# Station Groups
groups = {
    'West': ['LGPZ', 'LGRX', 'LGAD', 'LGKL'],
    'Central': ['LGLR', 'LGBL', 'LGTG', 'LGEL', 'LGTT', 'LGSA'],
    'East': ['LGTS', 'LGKV', 'LGLM', 'LGSY', 'LGSR', 'LGTL'],
    'Turkey': ['LTBG', 'LTBF', 'LTBT', 'LTBI', 'LTBS', 'LTAN']
}

prev_message = ""

def fetch_metar_data(station):
    """Fetch METAR data from the database for a given station."""
    sql_query = f"""
        SELECT Ginput, Gtext 
        FROM MyDSA 
        WHERE Gheader LIKE '%SAGR89 {station}%'
        OR Gheader LIKE '%SPGR91 {station}%'
        OR Gheader LIKE '%SAGR21 {station}%'
        OR ((Gheader LIKE '%SATU21 LTAA%' OR Gheader LIKE '%SATU22 LTAA%' OR Gheader LIKE '%SATU31 LTAA%') 
        AND Gtext LIKE '%{station}%')
    """
    cursor.execute(sql_query)
    return cursor.fetchall()

def process_metar(row):
    """Process a single METAR row and extract key data points."""
    initial_timestamp = datetime.datetime(
        int(row[0][:4]), int(row[0][4:6]), int(row[0][6:8]),
        int(row[0][8:10]), int(row[0][10:12])
    )
    full_date = initial_timestamp - datetime.timedelta(minutes=10)
    
    name = row[1][:4]
    hour, minute = int(row[1][7:9]), int(row[1][9:11])
    full_date = full_date.replace(hour=hour, minute=minute)

    if name == 'LGTT' and full_date.minute in [0, 30]:
        full_date -= datetime.timedelta(minutes=10)

    return name, full_date, row[1]

def analyze_metar_data(message):
    """Parse METAR message and extract useful information."""
    metar = MetarParser().parse(message)
    
    temperature = metar.temperature
    visibility = h.getvisibility(metar.visibility)
    wind_speed = metar.wind.gust if metar.wind.gust and metar.wind.gust > 35 else (metar.wind.gust + metar.wind.speed) / 2 if metar.wind.gust else metar.wind.speed
    weather_text = h.getweather(metar.weather_conditions)
    
    cloud_info = str(metar.clouds)
    contains_tcu = int('TCU' in cloud_info or 'CB' in cloud_info)

    # Extract weather intensity, phenomenon, description
    if metar.weather_conditions:
        conditions = metar.weather_conditions[0]
        intensity, descr, phenom = conditions.intensity.value if conditions.intensity else None, conditions.descriptive.value if conditions.descriptive else None, conditions.phenomenons[0].value if conditions.phenomenons else None
    else:
        intensity, descr, phenom = None, None, None

    return temperature, visibility, wind_speed, weather_text, contains_tcu, intensity, descr, phenom, metar.flags

def process_stations(group_name, stations):
    """Process METAR data for a group of stations and generate plots."""
    dicts_data, dicts_colors = {}, {}
    list_all_hours = []

    for station in stations:
        dict_data, dict_colors = OrderedDict(), OrderedDict()
        
        for row in fetch_metar_data(station):
            name, full_date, message = process_metar(row)

            global prev_message
            if message == prev_message:
                continue

            temp, vis, wind, weather_txt, contain_tcu, intensity, descr, phenom, flag = analyze_metar_data(message)
            colors = h.get_colors(temp, vis, wind, intensity, phenom, descr, contain_tcu, full_date, flag)

            dict_colors[full_date] = colors
            dict_data[full_date] = [message, weather_txt, wind, temp, vis]

            prev_message = message

        dicts_data[name] = dict_data
        dicts_colors[name] = dict_colors
        list_all_hours.extend(list(dict_data.keys()))

    list_all_hours = sorted(set(list_all_hours))

    return dicts_data, dicts_colors, list_all_hours

def generate_plots(group_name, dicts_data, dicts_colors, list_all_hours):
    """Generate METAR visualization using Plotly."""
    tables, column_widths, header_font_sizes = [], [], []

    for name_key, dict_data in dicts_data.items():
        dict_colors = dicts_colors[name_key]

        for l_hour in list_all_hours:
            if l_hour not in dict_data:
                prev_hour = h.get_prev_time(l_hour, dict_colors.keys())
                dict_colors[l_hour] = dict_colors[prev_hour]
                dict_data[l_hour] = ['*', '*', '*', '*', '*']

        df = pd.DataFrame.from_dict(dict_data, orient='index', columns=['Message', 'Phenomenon', 'Wind', 'Temp', 'Vis']).sort_index()
        df_color = pd.DataFrame.from_dict(dict_colors, orient='index', columns=['Phenomenon', 'Wind', 'Temp', 'Vis']).sort_index()

        table_data = np.vstack((np.array([['PRECI', 'WIND', 'TEMP', 'VIS']]), h.filter_df_to_numpy(df)))
        table_data = table_data.transpose()

        header_list = [name_key] + [f"{(h + datetime.timedelta(minutes=10)).hour}Ζ" if i % 3 == 0 else f"{h.hour}:{h.minute}" for i, h in enumerate(list_all_hours)]
        column_widths.extend([0.7 if i % 3 == 0 else 0.5 for i in range(len(header_list))])
        header_font_sizes.extend([18 if i % 3 == 0 else 8 for i in range(len(header_list))])

        table = go.Table(
            columnwidth=column_widths,
            header=dict(values=header_list, fill_color='lightskyblue', align='center', font=dict(size=header_font_sizes)),
            cells=dict(values=table_data, fill_color=df_color.transpose().values, align='center')
        )

        tables.append(table)

    fig = go.Figure(data=tables)
    fig.write_image(f"{group_name}.png", width=2000, height=1000, scale=4)

# Run the processing for each station group
for group, stations in groups.items():
    dicts_data, dicts_colors, list_all_hours = process_stations(group, stations)
    generate_plots(group, dicts_data, dicts_colors, list_all_hours)

cursor.close()
conn.close()
