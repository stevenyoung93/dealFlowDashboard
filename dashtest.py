import numpy as np
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
from dash import Dash, dcc, html, Input, Output, callback, dash_table

################# Remove this pre-processing part for the upload vvvvvv
#df_deals = pd.read_excel("DealsMarNov.xlsx")
url = 'https://raw.githubusercontent.com/stevenyoung93/dealFlowDashboard/main/DealsMarNov.xlsx'
df_deals = pd.read_excel(url, index_col=0)

# Convert the dates column to datetime type
df_deals ['Date'] = pd.to_datetime(df_deals ['Date'], format='%B %d, %Y')
df_descr = df_deals[['Name', 'Date', 'Series', 'Description']]

df_descr ['Date'] = pd.to_datetime(df_descr['Date'])

df = df_deals[['Date', 'Amount_number', 'Series', 'Name']]

df['Month'] = df['Date'].apply(lambda x: x.strftime("%m"))
df.Month = df.Month.astype(int)

################# Remove this pre-processing part for the upload ^^^^^^^

# Load in and generate (copies of) different data tables for underlying views
df = df.groupby(['Date', 'Month', 'Series', 'Name'], as_index=False).sum()
df_monthly = df.groupby(['Month', 'Series'], as_index=False).sum()

df_count = df[['Date', 'Month', 'Series', 'Amount_number']].groupby(['Date', 'Series',], as_index=False).count()
df_count_monthly = df[['Date', 'Month', 'Series', 'Amount_number']].groupby(['Month', 'Series'], as_index=False).count()

# Initialize dash app
app = Dash(__name__)
server = app.server

# Define layout/hierarchy
app.layout = html.Div([
    # Header and selections for the interactive plots
    html.H1('Venture deals in 2022 (full March to November)'),   
    html.Div([
        html.Div('''Select range of months to look into'''),
        html.Br(),
        dcc.RangeSlider(
            df['Month'].min(), df['Month'].max(), 1, value=[df['Month'].min(), df['Month'].max()], 
            id='my-range-slider'),
    ],
    style={'width': '44%', 'display': 'inline-block'}),
        
    html.Div([
    ],
    style={'width': '9%', 'display': 'inline-block'}),
    
    html.Div([
        html.Div('''Select scales for plots'''), 
        dcc.RadioItems(
            ['Linear', 'Log'],
            'Linear',
            id='yaxis-type',
            inline=True
        ),
    ],
    style={'width': '22%', 'display': 'inline-block'}),
    
    html.Div([
        html.Div('''Select aggregation level of data'''),
        dcc.RadioItems(
            ['Daily (no aggregration)', 'Monthly'],
            'Daily (no aggregration)',
            id='aggregation-selection',
            inline=True
        ),
    ],
    style={'width': '22%', 'display': 'inline-block'}),
    
    html.Br(),
    html.Br(),
    html.Div([
        html.Div('''Select funding series'''),
        dcc.Checklist(
            options=np.unique(df.Series),
            value=['Series A', 'Series B'],
            id='series-selection',
            inline=True
        ),
    ],
    style={'width': '99%', 'display': 'inline-block'}),
    
    html.Div([
        dcc.Graph(id='graph-with-slider'),
    ],
    style={'width': '49%', 'display': 'inline-block'}),
    html.Div([
        dcc.Graph(id='graph-with-slider2'),
    ],
    style={'width': '49%', 'display': 'inline-block'}),

    # testing area
    html.Div(id='tester1'),
    
    # Create table which will be filtered down based on selection above
    dbc.Label('Click a cell in the table:'),
    dash_table.DataTable(df_descr.to_dict('records'),[{"name": i, "id": i} for i in df_descr.columns], style_cell={'textAlign': 'left'}, id='tbl'),
    dbc.Alert(id='tbl_out'),
    html.Div('''Need to find out how to return from callback into filtered table and how to return sum within interactive limits''')
])


# Write callbacks that change graph and table given inputs from the sliders and selections
@app.callback(    
    Output('graph-with-slider', 'figure'),
    Output('graph-with-slider2', 'figure'),
    [Input('my-range-slider', 'value')],
    [Input('series-selection', 'value')],
    Input('aggregation-selection', 'value'),
    Input('yaxis-type', 'value'))
def update_output(months, series_selection, aggregation_selection, yaxis_type):  
    if aggregation_selection == 'Daily (no aggregration)':
        mask = (df_count.Month >= months[0]) & (df_count.Month <= months[1]) & df.Series.apply(lambda x: True if x in series_selection else False)
        filtered_df = df.loc[mask]
        mask_count = (df_count.Month >= months[0]) & (df_count.Month <= months[1]) & (df_count.Series.apply(lambda x: True if x in series_selection else False))
        filtered_df_2 = df_count.loc[mask_count]
        fig = px.scatter(filtered_df, x="Date", y="Amount_number",
                         hover_name="Name", color="Series",
                         labels={
                             "Date": "Date (Month Day, Year)",
                             "Amount_number": "Funding amount ($m)",
                             "Series": "Funding series stage"
                         }, title ="Amount of VC funding over time")
                         
        fig2 = px.scatter(filtered_df_2, x="Date", y="Amount_number", color="Series",
                         labels={
                             "Date": "Date (Month Day, Year)",
                             "Amount_number": "Number of deals",
                             "Series": "Funding series stage"
                         }, title ="Number of VC deals over time")
    else:
        mask = (df_monthly.Month >= months[0]) & (df_monthly.Month <= months[1]) & (df_monthly.Series.apply(lambda x: True if x in series_selection else False))
        filtered_df = df_monthly.loc[mask]
        mask_count = (df_count_monthly.Month >= months[0]) & (df_count_monthly.Month <= months[1]) & (df_count_monthly.Series.apply(lambda x: True if x in series_selection else False))
        filtered_df_2 = df_count_monthly.loc[mask_count]
        fig = px.line(filtered_df, x="Month", y="Amount_number", color="Series",
                         labels={
                             "Month": "Month",
                             "Amount_number": "Funding amount ($m)",
                             "Series": "Funding series stage"
                         }, title ="Amount of VC funding over time")
                         
        fig2 = px.bar(filtered_df_2, x="Month", y="Amount_number", 
                      color="Series", barmode="group",
                         labels={
                             "Date": "Date (Month Day, Year)",
                             "Amount_number": "Number of deals",
                             "Series": "Funding series stage"
                         }, title ="Number of VC deals over time")

    # fix y limits to make it look better
    if yaxis_type == 'Linear':
        fig.update_yaxes(type='linear')
        fig.update_layout(yaxis_range=[0,int(1.1*max(filtered_df.Amount_number))])
        fig2.update_yaxes(type='linear')
        fig2.update_layout(yaxis_range=[0,int(1.1*max(filtered_df_2.Amount_number))+1])
    else:
        fig.update_yaxes(type='log')
        fig2.update_yaxes(type='log')
    fig.update_layout(transition_duration=500)
    
    return fig, fig2


@callback(Output('tbl_out', 'children'), Input('tbl', 'active_cell'))
def update_graphs(active_cell):
    return str(active_cell) if active_cell else "Click the table"


if __name__ == '__main__':
    app.run_server(debug=True)
