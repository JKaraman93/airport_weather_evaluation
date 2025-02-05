import datetime

def date_to_str(ddate):
    str_date = []
    for i in ddate:
        str_d = str(i.hour) + ':' + str(i.minute) + 'Z'
        str_date.append(str_d)
    return str_date


def getclouds(clouds):
    c_text = ''
    for c in clouds:  # for i in range(len(clouds))
        c_height = c.height / 100
        if c_height >= 100:
            c_height = str(int(c_height))
        elif c_height >= 10:
            c_height = '0' + str(int(c_height))
        else:
            c_height = '00' + str(int(c_height))
        c_text = c_text + c.quantity.name + c_height + ' '
    return c_text

def getvisibility(vis):
    if vis:
        try:
            vis_d = int(vis.distance[:-1])
        except:
            vis_d = 10000
        if not vis.min_distance:
            vis_min = 10000
        else:
            vis_min = vis.min_distance
        return min(vis_d,vis_min)
    else:
        return None

def check_wind(w, ddate):
    night = datetime.datetime(ddate.year, ddate.month, ddate.day, 15,0)
    morning = datetime.datetime(ddate.year, ddate.month, ddate.day, 3,0)

    if w>=0:
        if w>35:
            return 'red'
        elif w>=20:
            return 'yellow'
        elif w>=15 and (ddate >= night or ddate <= morning):
            print(ddate, night)
            return 'yellow'
        else:
            return 'green'
    else:
        return 'white'

def check_vis(vis):
    if vis:
        if vis<1000:
            return 'red'
        elif vis<=5000:
            return 'yellow'
        else:
            return 'green'
    else:
        return 'white'



def check_phenom(intensity, phenom, descr, contain_tcu, flag):
    if len(flag)==1:
        return 'white'
    if intensity=='RE':
        if contain_tcu == 1:
            return 'palegoldenrod'
        else:
            return 'green'
    if descr:
        if descr=='TS':
            return 'red'
    if (contain_tcu == 1) and (phenom == 'RA'):
        return 'orange'
    if contain_tcu == 1:
        return 'palegoldenrod'
    if phenom =='RA':   ## correction need
        if intensity != '-':
            return 'yellow'
    if phenom =='SN':
        if intensity == '-':
            return 'cyan'
        else:
            return 'blue'
    return 'green'

def check_temp(temp):
    if temp:
        if temp <=-5 or temp>38:
            return 'red'
        elif temp<0:
            return 'yellow'
        else:
            return 'green'
    else:
        return 'white'

def get_colors (temp, vis, w_sp, intensity, phenom, descr, contain_tcu,date,flag ):
    return (check_phenom(intensity,phenom,descr,contain_tcu, flag), check_wind(w_sp,date), check_temp(temp), check_vis(vis))  #white for date, grey for message
    #return ('gray', check_phenom(intensity,phenom,descr,contain_tcu), check_wind(w_sp, date), check_temp(temp), check_vis(vis))  #white for date, grey for message

def getweather(weather):
    w_text = ''
    for w in weather:
        try:
            w_intens = w.intensity.value
        except:
            w_intens = ''
        try:
            w_descr = w.descriptive.value
        except:
            w_descr = ''
        try:
            w_phenom = w.phenomenons[0].value
        except:
            w_phenom = ''
        w_text = w_text + w_intens + w_descr + w_phenom + ' '
    return w_text

def get_prev_time(speci, time_dict):
    timestamps = sorted(time_dict)  # Sort the timestamps
    previous_timestamp = timestamps[0]

    for ts in timestamps:
        if ts < speci:
            previous_timestamp = ts
        else:
            break
    return previous_timestamp

def filter_df_to_numpy(df):
    df = df.drop(columns=['Message'], axis=1)
    # Create a copy of the DataFrame
    filtered_df = df.copy()

    # Replace non-matching cells with NaN
    filtered_df = filtered_df.where(filtered_df == '*', '')

    # Convert the DataFrame to a NumPy array
    return filtered_df.to_numpy()