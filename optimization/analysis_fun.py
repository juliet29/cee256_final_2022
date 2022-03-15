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


def saveImagePlotly(fig, fig_name):
    fig_name_png = fig_name + ".png"
    # fig_path = os.path.join(root, "figs_final_pres_03_07", fig_name_png )
    final_paper_path = "/Users/julietnwagwuume-ezeoke/My Drive/CEE256_BuildSys/final_256/Deliverables/PaperFigs"
    fig_path = os.path.join(final_paper_path, fig_name_png)
    fig.write_image(fig_path, width=1200, format="png", engine="kaleido",
                    scale=2)


def timestamp():
    now = datetime.now()
    now_string = now.strftime("%m_%d__%H_%M_%S")
    return now_string


def calc_marker_size(arr, curr_index):
    return max(len(arr)*2 - (curr_index+1)*1.999, 0)


def four_compare(group_keys, group_data, group_of_interest, group_labels):
    shades = px.colors.qualitative.Vivid[:len(group_keys)]

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Energy Consumption vs Adjusted Values",
            "Energy Consumption vs Percent Change",
            "Energy Savings vs Cost Savings",
            "Energy Savings vs Adjusted Values",
            # "Cost Savings vs Adjusted Values"
        ))

    # plot 1
    for (ix, k), shade in zip(enumerate(group_data.keys()), shades):
        y = group_data[k]["total"]
        x = group_data[k]["imperial_vals"]
        name = group_labels[k]
        marker_size = calc_marker_size(x, ix)
        fig.add_trace(go.Scatter(x=x, y=y, name=name, mode='lines+markers', marker_size=marker_size,
                                 legendgroup="Groups", showlegend=True, line=dict(color=shade)),
                      row=1, col=1)
    fig['layout']['xaxis']['title'] = "Adjusted Values"
    fig['layout']['yaxis']['title'] = "Energy [kWh]"

    # fig.update_layout(legend=dict(
    #     yanchor="bottom",
    #     y=-0.05,
    #     xanchor="center",
    #     x=0
    # ))

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
        x = group_data[k]["imperial_vals"]
        y_ = group_data[k]["total"] - group_data[k].loc[0]["total"]

        # concentrate on possibility of savings
        y = [-1*min(val, 0) for val in y_]

        marker_size = calc_marker_size(x, ix)
        fig.add_trace(go.Scatter(x=x, y=y, name=k, mode='lines+markers', marker_size=marker_size,
                                 legendgroup="Groups", showlegend=False, line=dict(color=shade)),
                      row=2, col=2)
    fig['layout']['xaxis4']['title'] = "Adjusted Values"

    # # # plot 5
    # for (ix, k), shade in zip(enumerate(group_data.keys()), shades):
    #     x = group_data[k]["vals"]
    #     y_ = group_data[k]["total_c"] - group_data[k].loc[0]["total_c"]

    #     # concentrate on possibility of savings
    #     y = [-1*min(val, 0) for val in y_]

    #     marker_size = calc_marker_size(x, ix)
    #     fig.add_trace(go.Scatter(x=x, y=y, name=k, mode='lines+markers', marker_size=marker_size,
    #                              legendgroup="Groups", showlegend=False, line=dict(color=shade)),
    #                   row=3, col=1)
    # fig['layout']['xaxis5']['title'] = "Values"
    # fig['layout']['xaxis5']['title'] = "Cost Savings [$]"

    fig.update_layout(title=f"Comparisons for {group_of_interest}")

    fig.show()

    # # make public
    # time = timestamp()
    fig_name = f"{group_of_interest}_raw"
    link = py.plot(
        fig, filename=f"{group_of_interest}_raw", auto_open=False)
    print("Link ", link)

    # save image
    saveImagePlotly(fig, fig_name)

    return fig


def correlations(group_data, group_of_interest):
    # calculate correlations
    fig = go.Figure()

    corr_data = {}
    for k in group_data.keys():
        corr_df = group_data[k][["total", "imperial_vals"]].corr()
        corr_data[k] = corr_df.loc["imperial_vals"]["total"]

    fig.add_trace(go.Bar(x=list(corr_data.keys()), y=list(corr_data.values())))
    fig.update_layout(xaxis_title=f"Groups",
                      yaxis_title="Correlation",
                      title="Correlation between Value and Energy Use")

    fig.show()

    # # make public
    # time = timestamp()
    # link = py.plot(
    #     fig, filename=f"{group_of_interest}_corr", auto_open=False)
    # print("Link ", link)
