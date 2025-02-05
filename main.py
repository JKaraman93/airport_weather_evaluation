import pyodbc
import datetime
from metar_taf_parser.parser.parser import MetarParser
import pandas as pd
import os
import numpy as np
import plotly.graph_objects as go
import helpers as h
from collections import OrderedDict

# TODO
# 1. Ignore past weather e.g RERA --DONE!
# 2. Transpose go.Table, dates as headers (! too long string)  --DONE!
# 3. Save figures --DONE!
# 4. Improve code sufficiency (e.g if temp:  etc)
# 5. ERROR in case of correction METARS   --ALMOST DONE!
# 6. Return average of max and mean wind   --DONE!
# 7. Handle TCU clouds as orange warning  --DONE
# 8. Handle cases with more phenomenons, not just one
# 9. Handle cases with temperatures Μ00   -- DONE   .venv/Lib/site-packages/metar_taf_parser/commons/converter.py ,  line 20 , return -int(input.split('M')[1])-0.001
# 10. Include legend --DONE
# 11. Exclude row with messages in table --DONE


#path = r'C:\Users\tolis\T20250204.MDB'
#path = r'C:\Users\Jim\Desktop\Archive\2023\2023_01\METEOImages_20230101\T20230101.MDB'
path = r'C:\Users\tolis\T20250113.MDB'
conn = pyodbc.connect(r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=' + path + ';')
cursor = conn.cursor()
stations = ['LGPZ','LGRX', 'LGAD', 'LGKL', 'LGLR', 'LGTS', 'LGBL', 'LGTG', 'LGEL', 'LGSA', 'LGTL', 'LGLM', 'LGSY', 'LGSR',
            'LGSM', 'LTBG', 'LTBF', 'LTBT', 'LTBI', 'LTBS', 'LTAN']

prev = ''
west = ['LGPZ','LGRX', 'LGAD', 'LGKL',]
central = ['LGLR', 'LGBL', 'LGTG', 'LGEL','LGTT', 'LGSA',]
east = [ 'LGTS', 'LGKV' ,'LGLM', 'LGSY', 'LGSR','LGTL',]
turkey = ['LTBG','LTBF', 'LTBT', 'LTBI', 'LTBS','LTAN']
groups = {'West':west, 'Central':central, 'East':east, 'Turkey':turkey}

for g in groups.keys() :
    tables = []
    list_all_hours = []
    dicts_data = {}
    dicts_colors = {}
    column_widths = []
    header_font_sizes = []
    for sind , s in enumerate (groups[g]):
        dict_ = OrderedDict()
        dict_c = OrderedDict()

        cursor.execute(  # "SELECT Ginput,Gtext FROM MyDSA where Gtext like '%{s}%'".format(s=s))
            "SELECT Ginput,Gtext FROM MyDSA where Gheader like '%SAGR89 {s}%' OR Gheader like '%SPGR91 {s}%' OR Gheader like '%SAGR21 {s}%' "
            "OR ((Gheader LIKE '%SATU21 LTAA%' OR Gheader LIKE '%SATU22 LTAA%' OR Gheader LIKE '%SATU31 LTAA%') AND Gtext LIKE '%{s}%')".format(s=s))

        # "SELECT Ginput,Gtext FROM MyDSA where Gtext like '%'+s+'%'")
       #rows = [('20240502235306435', 'LGRX 022350Z 00000KT 9999 -SNRA SCT035 Μ16/16 Q1013 RETS [METAR]='),
           #     ('20240502235306435', 'LGRX 022250Z 36036KT 7000 SCT035CB M00/16 Q1013 [METAR] ='),
       #         ('20240502225306435', 'LGRX 022320Z 01014G24KT 5000 +SHRA FEW012TCU  00/16 Q1013 [METAR]=')]

        for row in cursor.fetchall():
        #for row in rows:
            print(row)
            initial_timestamp = datetime.datetime(int(row[0][:4]), int(row[0][4:6]), int(row[0][6:8]), int(row[0][8:10]),
                                                  int(row[0][10:12]))
            
            # Subtract 10 minutes using timedelta : time threshold to get sent a metar
            full_date = initial_timestamp - datetime.timedelta(minutes=10)
            name = row[1][:4]

            year = full_date.year
            month = full_date.month
            day = full_date.day
            message = row[1]
            hour = int(row[1][7:9])
            minute = int(row[1][9:11])
            full_date = full_date.replace(hour=hour, minute=minute)
            if name == 'LGTT':
                if full_date.minute in [0, 30]:
                    if full_date.hour == 0 and full_date.minute == 0:
                        continue
                    else:
                        full_date -= datetime.timedelta(minutes=10)
            #message = 'LGTL 012050Z 00000KT //// // ////// 10/// Q1029   RE// [METAR]='
            metar = MetarParser().parse(message)
            flag=metar.flags
            temp = metar.temperature
            vis = h.getvisibility(metar.visibility)
            contain_tcu = (str(metar.clouds))
            if 'TCU' in contain_tcu or 'CB' in contain_tcu :
                contain_tcu = 1
            if metar.wind.gust:
                if metar.wind.gust > 35:
                    w_sp = metar.wind.gust
                else:
                    w_sp = (metar.wind.gust + metar.wind.speed) / 2
            else:
                w_sp = metar.wind.speed
            weather_txt = h.getweather(metar.weather_conditions)
            if metar.weather_conditions:
                intensity = metar.weather_conditions[0].intensity
                if intensity:
                    intensity = intensity.value

                if metar.weather_conditions[0].descriptive:
                    descr = metar.weather_conditions[0].descriptive.value
                else:
                    descr = None
                if metar.weather_conditions[0].phenomenons:
                    phenom = metar.weather_conditions[0].phenomenons[0].value
                else:
                    phenom = None
            else:
                intensity = None
                phenom = None
                descr = None
            if message != prev:
                # print (s, full_date, temp, dew_point, di)
                colors = h.get_colors(temp, vis, w_sp, intensity, phenom, descr, contain_tcu, full_date,flag)
                dict_c[full_date] = colors
                dict_[full_date] = [message, weather_txt, w_sp, temp, vis]

            prev = message
        dicts_data[name] = dict_
        dicts_colors[name] = dict_c

        list_all_hours.extend(list(dict_.keys()))
    list_all_hours = list(set(list_all_hours))
    list_all_hours.sort()
    
 
    for sind, name_key in enumerate(list(dicts_data.keys())):
        dict_ = dicts_data[name_key]
        dict_c = dicts_colors[name_key]
        for l_hour in list_all_hours:
            if l_hour not in list(dict_.keys()):
                prev_hour = h.get_prev_time(l_hour,dict_c.keys())
                dict_c[l_hour] = dict_c[prev_hour]

                dict_[l_hour] = ['*','*', '*', '*','*']

                #dict_c[l_hour] = ('gray', 'gray', 'gray', 'gray')
                #dict_[l_hour] = ['','', '', '','']
        df = pd.DataFrame.from_dict(dict_, orient='index', columns=['Message', 'Phenomenon', 'Wind', 'Temp', 'Vis']).sort_index()
        df_color = pd.DataFrame.from_dict(dict_c, orient='index',
                                          columns=[ 'Phenomenon', 'Wind', 'Temp', 'Vis']).sort_index()


        copy_df=h.filter_df_to_numpy(df)
        array1 = np.array([[ 'PRECI', 'WIND', 'TEMP', 'VIS']])  # Shape (1, 4)
        k = np.vstack((array1,copy_df ))

        '''     
        k = [[ 'PRECI', 'WIND', 'TEMP', 'VIS']]
        for m in df.Message.values:
            new_column = []
            new_column.extend([''] * 4)
            k.append(new_column)
        k = np.array(k)
        '''
        k_tr = k.transpose()

        header_list = [name_key]
        #header_list.extend(date_to_str(list_all_hours))
        header_list.extend(list_all_hours)
        df_tr = df_color.transpose()
        df_tr.insert(0, 'col1', ['lightblue'] * len(df_color.columns))

        #line_widths = [5 if (i % 4 == 0 and i != 0) else 1 for i in range (len(header_list))]

        list_3h = [datetime.datetime(year = header_list[1].year,month= header_list[1].month, day= header_list[1].day,hour=i,minute=50) for i in range (2,21,3)]
        trial_list = header_list
        for i, header in enumerate(header_list):
            if header not in list_3h:
                if i!=0:
                    header_list[i] = str(header.hour) + ':' + str(header.minute)
                else:
                    header_list[i] = ''
                column_widths.append(0.5)
                header_font_sizes.append(8)

            else:
                header_list[i]= str((header_list[i] + datetime.timedelta(minutes=10)).hour) + 'Ζ'
                column_widths.append(0.7)
                header_font_sizes.append(18)

        trial_list[0] = name_key
        column_widths[0] = 1
        header_font_sizes[0] = 18


        table = go.Table(
        columnwidth=column_widths,
        #domain=dict(y=[0., 0.98-0.07*sind]),  # Position this table in the lower half
        domain=dict(y=[0., 0.95-0.15*sind]),  # Position this table in the lower half

            header=dict(values=header_list,
                #values=trial_list,
                        line_color='darkslategray',
                        #line_width=line_widths,
                        fill_color='lightskyblue',
                        align='center',
                        height=30,
                        font=dict(size=header_font_sizes ),
                        ),

            cells=dict(values=k,
                       line_color='darkslategray',
                       fill_color=df_tr.transpose(),  # df_color.to_numpy().transpose(),
                       align='center',
                       #line_width=line_widths,
            )
        )

        tables.append(table)
            
    # Add a scatter plot as the legend
    legend_colors = ['red','orange','yellow','palegoldenrod','blue','cyan', 'white']
    legend_labels = ['TS','CONV+RA','RA','CONV','SN','-SN', 'NoData']
    scatter_legend = [
        go.Scatter(
            x=[None],  # No actual data points
            y=[None],
            mode='markers',
            marker=dict(
                size=15,
                color=color,
                line=dict(
                    color='black',
                    width=0.5
                )
            )

        ,
            name=label, # Label for the legend
            showlegend = True,
            #opacity = 0  # Hide the markers on the plot
        )
        for color, label in zip(legend_colors, legend_labels)
    ]

    # Create the figure
    #fig = go.Figure(data=tables + scatter_legend)
    fig = go.Figure(data=tables + scatter_legend)

    fig_name = g + '_' + str(day)+'-'+ str(month)+'-'+str(year)
    print (fig_name)
    fig.update_layout(
        title=dict(
            text=fig_name,
            x=0.5,
            xanchor="center",
            yanchor="top",
            font=dict(
                size=20,
                color="black"
            )
        ),
        #autosize=False,
        #width=1900,
        #height=2500,
        legend=dict(
            #title="Color Legend",
            orientation="h",
            x=0.12,
            xanchor="center",
            y=1.0  # Position below the table
        ),
        xaxis=dict(visible=False),  # Hide X-axis
        yaxis=dict(visible=False),  # Hide Y-axis
        plot_bgcolor="white",  # Set background to white
        paper_bgcolor="white"  # Ensure entire figure background is white

    )
    #fig.show()
    fig.write_image(fig_name+".png", width=2000, height=1000, scale=4)
    break

cursor.close()
conn.close()

