from dash import Dash, html, dcc
from dash import dash_table
import plotly.express as px
import pandas as pd
import numpy as np
import plotly.figure_factory as ff
from scipy.stats import iqr
from scipy import stats
from dash.dependencies import Input, Output
from scripts.utils import create_time_diff_group

dat = pd.read_csv("./sample_tracking.csv")


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.H2(children='Procedure Tracking - Gantt chart'),
    html.Div([
        "Tasks: ",
        dcc.Dropdown(dat['order'].tolist(), ['001', '002', '003'],
                     id='task-dropdown', multi = True),
        "Time pairs: ",
        dcc.Dropdown(dat.columns.tolist(), value=['analysis_starts', 'analysis_ends', 
                                                  'seq_starts', 'data_delivered', 
                                                  'case_created', 'report_signed_out'],
                     id='time-pair', multi = True),
    ]),
          
    dcc.Graph(
        id='gantt-chart-visualization'
    ),
    

    html.H2(children='Procedure Tracking - histogram'),
    html.Div([
        "Time pairs: ",
        dcc.Dropdown(dat.columns.tolist(), value=['specimen_collected', 'exp1_start_time', 
                                                  'specimen_collected', 'exp2_start_time'],
                     id='time-pair-1', multi = True),
    ]),
    
    dcc.Graph(
        id='distplot-visualization'
    ),
    

    html.H2(children='Procedure Tracking - outlier '),
    html.Div([
        "Time stamp start: ",
        dcc.Dropdown(dat.columns.tolist(), value='specimen_collected',
                     id='time-stamp-1', ),
        "Time stamp end: ",
        dcc.Dropdown(dat.columns.tolist(), value='exp1_start_time',
                     id='time-stamp-2', ),]),
    html.H3(children='IQR method'),
    html.Div([
        "IQR multiplier: ",
        dcc.Slider(0.1, 3.5, 0.1, value=0.5, marks=None, tooltip={"placement": "bottom", "always_visible": True}, 
                  id = 'slider-1', vertical = True, verticalHeight = 100),
        dash_table.DataTable(id = 'table-1', style_as_list_view=True, 
                             style_cell={'padding': '5px'}, 
                             style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'},
                             page_size=6,
                             )
                             
    ]),
    html.H3(children='Z score method'),
    html.Div([
        "Z score threshold: ",
        dcc.Slider(0.5, 6, 0.5, value=2, marks=None, tooltip={"placement": "bottom", "always_visible": True},
                  id = 'slider-2', vertical = True, verticalHeight = 100),
        dash_table.DataTable(id = 'table-2', style_as_list_view=True, 
                             style_cell={'padding': '5px'}, 
                             style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'},
                              page_size=6,
                            )
                        
    ]),
    
])
    


@app.callback(
    Output(component_id='gantt-chart-visualization', component_property='figure'),
    Input(component_id='task-dropdown', component_property='value'),
    Input(component_id='time-pair', component_property='value'),)
def gantt_visualization(tasks, time_stamp_pairs):
    """
    :param tasks: the list of tasks e.g. epic_orders = ['001', '002', '003']
    : param time_stamp_pairs: the list of pair of column names correspond to time stamps e.g. 
      interest_time_stamps = ['analysis_starts', 'analysis_ends', 
                            'seq_starts', 'data_delivered', 
                            'case_created', 'report_signed_out']
    """    
    df_gantt = []
    
    for order in tasks:
        dat_tmp = dat[dat['epic_order'] == order]
        
        for i in range(0, len(time_stamp_pairs), 2):
            df_gantt.append(dict(Task = order, Start = pd.to_datetime(dat_tmp[time_stamp_pairs[i]].tolist()[0]), 
                                 Finish = pd.to_datetime(dat_tmp[time_stamp_pairs[i+1]].tolist()[0]), 
                                 Resource = time_stamp_pairs[i+1] + '-' + time_stamp_pairs[i]))
    
    fig = ff.create_gantt(df_gantt, index_col='Resource', group_tasks=True, show_colorbar=True)
    return fig




@app.callback(
    Output(component_id='distplot-visualization', component_property='figure'),
    Input(component_id='time-pair-1', component_property='value'),)
def distplot_visualization(interest_time_stamp_pairs):
    """
    :param interest_time_stamp_pairs: list of time stamps. 
      e.g. ['specimen_collected', 'exp1_start_time', 'specimen_collected', 'exp2_start_time']
    
    :return: group_labels: a list.
    """
    time_diff_group, group_labels = create_time_diff_group(interest_time_stamp_pairs, dat)
    hist_data = [i.dropna() for i in time_diff_group]
    rug_text = []
    for i in range(len(time_diff_group)):
        rug_text_tmp = time_diff_group[i].dropna().index
        rug_text_tmp = [dat['epic_order'][i] for i in rug_text_tmp]
        rug_text.append(rug_text_tmp)
    fig = ff.create_distplot(hist_data, group_labels, bin_size=.2, rug_text=rug_text)
    return fig
    
    
    

@app.callback(
    Output(component_id='table-1', component_property='data'),
    Input(component_id='time-stamp-1', component_property='value'),
    Input(component_id='time-stamp-2', component_property='value'),
    Input('slider-1', 'value'))    
def outlier_detect_IQR(time_stamp_1, time_stamp_2, multiplier_IQR): 
    """
    :param: time_stamp_1, time_stamp_2, the column names of the input csv file
    :return: a list of epic order ids for the outliers
    """
    t1 = pd.to_datetime(dat[time_stamp_1])
    t2 = pd.to_datetime(dat[time_stamp_2])
    time_diff = (t2 - t1).apply(lambda x: pd.Timedelta(x).seconds/3600)
    time_diff_noNa = time_diff.dropna()
    IQR = iqr(time_diff_noNa)
    Q1, Q3 = time_diff_noNa.quantile([0.25,0.75])
    low_bound = Q1 - multiplier_IQR * IQR
    up_bound = Q3 + multiplier_IQR * IQR
    low_ids = time_diff[time_diff < low_bound].index.tolist()
    up_ids = time_diff[time_diff > up_bound].index.tolist()
    ## NAs correspond to even longer time, since it hasn't been processed
    NA_ids = time_diff[np.isnan(time_diff)].index.tolist()
    
    if len(up_ids) > 0:
        up_ids += NA_ids
    else:
        up_ids = NA_ids
        
    if len(low_ids) > 0:
        outlier_orders = dat['epic_order'].iloc[low_ids + up_ids].tolist()
        outlier_time_diff = time_diff.iloc[low_ids + up_ids].tolist()
    else:
        outlier_orders = dat['epic_order'].iloc[up_ids].tolist()
        outlier_time_diff = time_diff.iloc[up_ids].tolist()
        
    outlier_orders = dat['epic_order'].iloc[low_ids + up_ids].tolist()
    outlier_time_diff = time_diff.iloc[low_ids + up_ids].tolist()
    
    df = pd.DataFrame({'outlier_orders': outlier_orders, 'outlier_time_diff': outlier_time_diff})
    data = df.to_dict(orient='records')
    return data





@app.callback(
    Output(component_id='table-2', component_property='data'),
    Input(component_id='time-stamp-1', component_property='value'),
    Input(component_id='time-stamp-2', component_property='value'),
    Input('slider-2', 'value'))
def outlier_detect_Zscore(time_stamp_1, time_stamp_2, zscore_threshold):
    t1 = pd.to_datetime(dat[time_stamp_1])
    t2 = pd.to_datetime(dat[time_stamp_2])
    time_diff = (t2 - t1).apply(lambda x: pd.Timedelta(x).seconds/3600)
    time_diff_zscores = stats.zscore(time_diff, nan_policy='omit')
    low_ids = time_diff[time_diff_zscores < (-1)*zscore_threshold].index.tolist()
    up_ids = time_diff[time_diff_zscores > zscore_threshold].index.tolist()
    NA_ids = time_diff[np.isnan(time_diff)].index.tolist()
    
    if len(up_ids) > 0:
        up_ids += NA_ids
    else:
        up_ids = NA_ids
    
    if len(low_ids) > 0:
        outlier_orders = dat['epic_order'].iloc[low_ids + up_ids].tolist()
        outlier_time_diff = time_diff.iloc[low_ids + up_ids].tolist()
    else:
        outlier_orders = dat['epic_order'].iloc[up_ids].tolist()
        outlier_time_diff = time_diff.iloc[up_ids].tolist()
        
    df = pd.DataFrame({'outlier_orders': outlier_orders, 'outlier_time_diff': outlier_time_diff})
    data = df.to_dict(orient='records')

    return data






if __name__ == '__main__':
    app.run_server(debug=False)

