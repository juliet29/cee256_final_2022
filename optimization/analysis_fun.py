import pandas as pd
import os
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime

import chart_studio
import chart_studio.plotly as py
import chart_studio.tools as tls

username = "jnwagwu"
api_key = "119wNvkoTSGwHIxORQ85"

chart_studio.tools.set_credentials_file(username=username, api_key=api_key)


def timestamp():
    now = datetime.now()
    now_string = now.strftime("%m_%d__%H_%M_%S")
    return now_string


def calc_marker_size(arr, curr_index):
    return max(len(arr)*2 - (curr_index+1)*1.999,0)


def four_compare(group_keys, group_data, group_of_interest):
    shades = px.colors.qualitative.Vivid[:len(group_keys)]

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Energy vs Adjusted Values",
            "Energy vs Percent Change",
            "Energy Savings vs Cost Savings",
            "Energy Savings vs Adjusted Values"
        ))

    # plot 1
    for (ix, k), shade in zip(enumerate(group_data.keys()), shades):
        y = group_data[k]["total"]
        x = group_data[k]["vals"]
        marker_size = calc_marker_size(x, ix)
        fig.add_trace(go.Scatter(x=x, y=y, name=k, mode='lines+markers', marker_size=marker_size,
                                 legendgroup="Groups", showlegend=True, line=dict(color=shade)),
                      row=1, col=1)
    fig['layout']['xaxis']['title'] = "Adjusted Values"
    fig['layout']['yaxis']['title'] = "Energy (kWh)"

    # # plot 2
    for (ix, k), shade in zip(enumerate(group_data.keys()), shades):
        y = group_data[k]["total"]
        x = group_data[k]["perc_change"]
        marker_size = calc_marker_size(x, ix)
        fig.add_trace(go.Scatter(x=x, y=y, name=k, mode='lines+markers', marker_size=marker_size,
                                 legendgroup="Groups", showlegend=False, line=dict(color=shade)),
                      row=1, col=2)
    fig['layout']['xaxis2']['title'] = "Percent Change from Original [%]"
    # fig['layout']['yaxis2']['title']="Energy (kWh)"

    # # plot 3
    for (ix, k), shade in zip(enumerate(group_data.keys()), shades):
        x_ = group_data[k]["total_c"] - group_data[k].loc[0]["total_c"]
        y_ = group_data[k]["total"] - group_data[k].loc[0]["total"]

        # concentrate on possibility of savings
        x = [-1*min(val, 0) for val in x_]
        y = [-1*min(val, 0) for val in y_]

        marker_size = calc_marker_size(x, ix)
        fig.add_trace(go.Scatter(x=x, y=y, name=k, mode='lines+markers', marker_size=marker_size,
                                 legendgroup="Groups", showlegend=False, line=dict(color=shade)),
                      row=2, col=1)
    fig['layout']['xaxis3']['title'] = "Cost Savings [$]"
    fig['layout']['yaxis3']['title'] = "Energy Savings [kWh]"

    # # plot 4
    for (ix, k), shade in zip(enumerate(group_data.keys()), shades):
        x = group_data[k]["vals"]
        y_ = group_data[k]["total"] - group_data[k].loc[0]["total"]

        # concentrate on possibility of savings
        y = [-1*min(val, 0) for val in y_]

        marker_size = calc_marker_size(x, ix)
        fig.add_trace(go.Scatter(x=x, y=y, name=k, mode='lines+markers', marker_size=marker_size,
                                 legendgroup="Groups", showlegend=False, line=dict(color=shade)),
                      row=2, col=2)
    fig['layout']['xaxis4']['title'] = "Values"

    fig.update_layout(title=f"Comparisons for {group_of_interest}")

    fig.show()

    # make public
    time = timestamp()
    link = py.plot(
        fig, filename=f"{group_of_interest}_raw", auto_open=False)
    print("Link ", link)


def correlations(group_data, group_of_interest):
    # calculate correlations
    fig = go.Figure()

    corr_data = {}
    for k in group_data.keys():
        corr_df = group_data[k][["total", "vals"]].corr()
        corr_data[k] = corr_df.loc["vals"]["total"]

    fig.add_trace(go.Bar(x=list(corr_data.keys()), y=list(corr_data.values())))
    fig.update_layout(xaxis_title=f"Groups",
                      yaxis_title="Correlation",
                      title="Correlation between Value and Energy Use")

    fig.show()

    # make public
    time = timestamp()
    link = py.plot(
        fig, filename=f"{group_of_interest}_corr", auto_open=False)
    print("Link ", link)
