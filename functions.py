import streamlit as st
import psycopg2, re
import networkx as nx
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

@st.experimental_memo
def get_graph_chart_data(_graph, artist_id2:int, artist_id1:int, artist_dict, album_dict):

    def get_marker_trace_sp(shortest_path, chart_graph, artist_dict, chart_colors, size_max):

        x = [node_pos[node][0] for node in shortest_path]
        y = [node_pos[node][1] for node in shortest_path]
        s = [chart_graph.nodes[node]['size'] for node in shortest_path]
        c = [chart_colors[node] for node in shortest_path]
        t = [artist_dict[node] for node in shortest_path]
        tp = ['top center' if size * 2  - len(text) * 14 < 3 else 'middle center' for text, size in zip(t, s)]

        trace = go.Scatter(
            x = x, 
            y = y, 
            hoverinfo = 'none', 
            text = t, 
            mode = 'markers+text',
            textposition = tp,
            textfont = dict(color='white', size=14),
            marker = dict(
                color = c,
                opacity = 1,
                size = s, 
                sizemin = 4,
                sizeref = 2.*size_max/(20**2),
                line = dict(
                    color = 'rgba(255, 255, 255, 0.2)', 
                    width = 8),
            ),
        )

        return trace

    def get_marker_trace_lo(layer_one_nodes, chart_graph, artist_dict, chart_colors, size_max):

        x = [node_pos[node][0] for node in layer_one_nodes]
        y = [node_pos[node][1] for node in layer_one_nodes]
        s = [chart_graph.nodes[node]['size'] for node in layer_one_nodes]
        c = [chart_colors[chart_graph.nodes[node]['parent']] for node in layer_one_nodes]
        t = [artist_dict[node] for node in layer_one_nodes]

        trace = go.Scatter(
            x = x, 
            y = y, 
            hoverinfo = 'text', 
            hoverlabel=dict(font_size=12, font=dict(color='white')),
            hovertemplate = [f'<b>{j}</b><extra></extra>' for j in t],
            text = t, 
            mode = 'markers',
            marker = dict(
                color = c,
                opacity = 0.5,
                size = s,
                sizemin = 4,
                sizeref = 2.*size_max/(20**2), 
                line = dict(width=2, color='rgba(255, 255, 255, 0.5)')
            ),


        )

        return trace

    def get_marker_trace_lt(layer_two_nodes, chart_graph, artist_dict, size_max):

        x = [node_pos[node][0] for node in layer_two_nodes]
        y = [node_pos[node][1] for node in layer_two_nodes]
        s = [chart_graph.nodes[node]['size'] for node in layer_two_nodes]
        c = ['gray' for node in layer_two_nodes]
        t = [artist_dict[node] for node in layer_two_nodes]

        trace = go.Scatter(
            x = x, 
            y = y, 
            hoverinfo = 'text', 
            hoverlabel=dict(font_size=12, font=dict(color='white')),
            hovertemplate = [f'<b>{j}</b><extra></extra>' for j in t],
            text = t, 
            mode = 'markers',
            marker = dict(
                color = c,
                opacity=0.1,
                size = s,
                sizemin = 4,
                sizeref = 2.*size_max/(20**2),
                line = dict(
                    width = 0),
            ),
        )
        
        return trace
    
    def get_edge_hover_trace_sp(shortest_path_edges, album_dict):

        x = [(node_pos[edge[0]][0] + node_pos[edge[1]][0]) / 2 for edge in shortest_path_edges]
        y = [(node_pos[edge[0]][1] + node_pos[edge[1]][1]) / 2 for edge in shortest_path_edges]
        t = [album_dict[chart_graph[edge[0]][edge[1]]['album_id']] for edge in shortest_path_edges]

        trace = go.Scatter(
            x = x, 
            y = y, 
            hoverinfo = 'text', 
            mode='markers',
            text = t, 
            marker = dict(opacity=0),
            hoverlabel = dict(bgcolor='white', font_size=14),
            hovertemplate = [f'<b>{j}</b><extra></extra>' for j in t],
        ) 
        
        return trace
    
    def get_edge_traces_sp(shortest_path_edges, chart_colors):
        
        traces = list()
        for i, edge in enumerate(shortest_path_edges):

            edge = tuple(sorted(edge))
            x0, y0 = node_pos[edge[0]]
            x1, y1 = node_pos[edge[1]]

            x = (x0 + x1) / 2
            y = (y0 + y1) / 2

            trace = go.Scatter(
                x=[x0, x, None], 
                y=[y0, y, None], 
                line=dict(width=5, color=chart_colors[edge[0]]), 
                hoverinfo='none',
                mode='lines',
            )

            traces.append(trace)

            trace = go.Scatter(
                x=[x, x1, None], 
                y=[y, y1, None], 
                line=dict(width=5, color=chart_colors[edge[1]]), 
                hoverinfo='none', 
                mode='lines',
            )

            traces.append(trace)
            
        return traces

    def get_edge_traces_lo(layer_one_edges, shortest_path, chart_colors):
        
        traces = list()
        for i, edge in enumerate(layer_one_edges):

            edge = tuple(sorted(edge))
            x0, y0 = node_pos[edge[0]]
            x1, y1 = node_pos[edge[1]]

            color = chart_colors[edge[0]] if edge[0] in shortest_path else chart_colors[edge[1]]

            trace = go.Scatter(
                x = [x0, x1, None], 
                y = [y0, y1, None], 
                line = dict(width=2, color=color), 
                opacity = 0.4,
                hoverinfo = 'none',
                mode = 'lines',
            )

            traces.append(trace)
        
        return traces
    
    def get_edge_trace_lt(layer_two_edges):
        
        x, y = list(), list()
        for edge in layer_two_edges:

            x0, y0 = node_pos[edge[0]]
            x1, y1 = node_pos[edge[1]]

            x.extend([x0, x1, None])
            y.extend([y0, y1, None])
            
        trace = go.Scatter(
            x = x, 
            y = y, 
            line=dict(width=1, color='grey'), 
            opacity=0.2,
            hoverinfo='none',
            mode='lines',
        )
        
        return trace
    
    chart_graph = _graph.copy()
    size_max = max([v for k, v in nx.get_node_attributes(chart_graph, 'size').items()])
    shortest_path = nx.shortest_path(chart_graph, artist_id1, artist_id2)
    nodes = list()

    # layer 0
    nx.set_node_attributes(chart_graph, {i: {'layer': 0, 'parent': None} for i in shortest_path})
    nodes += shortest_path

    layer_one_nodes = list()
    layer_two_nodes = list()
    for n in shortest_path:

        # layer 1
        nn1 = list(set(chart_graph.neighbors(n)) - set(shortest_path))
        nx.set_node_attributes(chart_graph, {j: {'layer': 1, 'parent': n} for j in nn1})
        layer_one_nodes += nn1

    for k in layer_one_nodes:

        # layer 2
        nn2 = list(set(chart_graph.neighbors(k)) - set(shortest_path) - set(layer_one_nodes))
        nx.set_node_attributes(chart_graph, {p: {'layer': 2, 'parent': p} for p in nn2})
        layer_two_nodes += nn2 

    nodes = set(shortest_path + layer_one_nodes + layer_two_nodes)

    # remove nodes
    remove_nodes = list(set(chart_graph.nodes) - nodes)
    chart_graph.remove_nodes_from(remove_nodes)

    print(chart_graph.number_of_nodes(), chart_graph.number_of_edges())

    centrality_threshold = min([nx.degree_centrality(chart_graph)[n] for n in shortest_path])
    remove_nodes = [k for k, v in nx.degree_centrality(chart_graph).items() if v < centrality_threshold]
    chart_graph.remove_nodes_from(remove_nodes)

    print(chart_graph.number_of_nodes(), chart_graph.number_of_edges())

    layer_one_nodes = [node for node in layer_one_nodes if node in chart_graph.nodes]
    layer_two_nodes = [node for node in layer_two_nodes if node in chart_graph.nodes]
    
    node_pos = nx.spring_layout(chart_graph, seed=1)
    
    colors = px.colors.sequential.Agsunset + px.colors.sequential.Bluyl
    chart_colors = colors[::len(colors) // len(shortest_path)]
    chart_colors = {node:chart_colors[i] for i, node in enumerate(shortest_path)}

    shortest_path_edges =  [tuple(sorted((shortest_path[i], shortest_path[i+1]))) for i in range(len(shortest_path) - 1)]
    layer_one_edges = [tuple(sorted(edge)) for edge in chart_graph.edges if (edge[0] in shortest_path or edge[1] in shortest_path) and (tuple(sorted(edge)) not in shortest_path_edges)]
    layer_two_edges = [tuple(sorted(edge)) for edge in chart_graph.edges if tuple(sorted(edge)) not in shortest_path_edges and tuple(sorted(edge)) not in layer_one_edges]
    
    marker_trace_sp = get_marker_trace_sp(shortest_path, chart_graph, artist_dict, chart_colors, size_max)
    marker_trace_lo = get_marker_trace_lo(layer_one_nodes, chart_graph, artist_dict, chart_colors, size_max)
    marker_trace_lt = get_marker_trace_lt(layer_two_nodes, chart_graph, artist_dict, size_max)
    edge_hover_trace_sp = get_edge_hover_trace_sp(shortest_path_edges, album_dict)
    edge_traces_sp = get_edge_traces_sp(shortest_path_edges, chart_colors)
    edge_traces_lo = get_edge_traces_lo(layer_one_edges, shortest_path, chart_colors)
    edge_trace_lt = get_edge_trace_lt(layer_two_edges)

    data = [edge_trace_lt, marker_trace_lt] + edge_traces_lo + [marker_trace_lo] + edge_traces_sp + [edge_hover_trace_sp, marker_trace_sp]
    
    return data

def get_graph_chart_layout():

    layout = go.Layout(
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        hovermode='closest',
        margin=dict(b=30,l=0,r=0,t=30),
        annotations=[dict(
            text="Source : <a href='https://genius.com'>Genius</a>",
            showarrow=False,
            xref="paper", yref="paper",
            x=0.005, y=-0.05,
            font=dict(color='white')
        )],
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
    )
    return layout

@st.experimental_memo
def get_artist_dict(_sql_cnx):

    query = f'SELECT artist_id, artist_name FROM artist'
    cursor = _sql_cnx.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    artist_dict = {i:re.sub('%27', '\"', re.sub('%22', '\'', v)) for i, v in result}

    return artist_dict

@st.experimental_memo
def get_album_dict(_sql_cnx):

    query = f'SELECT album_id, album_name FROM album'
    cursor = _sql_cnx.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    album_dict = {i:re.sub('%27', '\"', re.sub('%22', '\'', v)) for i, v in result}

    return album_dict

def query_to_dataframe(_sql_cnx, query, fillna=False):
    
    cursor = _sql_cnx.cursor()
    cursor.execute(query)
    df = cursor.fetchall()
    columns = [column.name for column in cursor.description]
    cursor.close()
    
    df = pd.DataFrame(df, columns=columns)
    for column in df.select_dtypes(include='object').columns:
        df[column] = df[column].str.replace('%27', '\"', regex=False).str.replace('%22', '\'', regex=False)
    
    if fillna:
        df.replace('NULL', np.NaN, inplace=True)

    return df

@st.experimental_singleton
def get_graph_filter_by_years(_graph, year_begin, year_end):
    
    remove_edges = [edge for edge, year in nx.get_edge_attributes(_graph, 'release_year').items() if pd.isnull(year) or int(year) < year_begin or int(year) > year_end]

    year_graph = _graph.copy()
    year_graph.remove_edges_from(remove_edges)
    
    return year_graph