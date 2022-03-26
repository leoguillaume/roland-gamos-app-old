from textwrap import shorten
from functions import *
import joblib

# CONFIG

st.set_page_config(
     page_title="Roland Gamos",
     page_icon="🎾",
     layout="centered",
     initial_sidebar_state="expanded",
     menu_items={
         'Report a bug': "https://www.extremelycoolapp.com/bug",
         'About': "# This is a header. This is an *extremely* cool app!"
     }
)

sql_cnx = psycopg2.connect(host="localhost", database="rapdashboard", user="leo")
G = joblib.load('graph.p')

lorem = 'Mauris lectus felis, aliquet ac urna et, cursus porta est. Sed non dictum arcu. Curabitur placerat ex sit amet magna scelerisque aliquet at pellentesque mauris. In facilisis diam at orci tempus, et tempor lacus euismod. Ut gravida felis diam, eget fringilla velit finibus non. Suspendisse pellentesque vitae tellus et cursus. Nulla facilisi.'

# MAIN

## INTRO
st.markdown('''
<style>
@import url('https://fonts.googleapis.com/css2?family=Merriweather+Sans:ital,wght@1,800&display=swap');
</style>
<h1 style="font-family: 'Merriweather Sans', sans-serif; font-weight: Extra-bold; color: rgb(85,26,139); font-size: 64px;"><i>LE ROLAND GAMOS</i></h1>
''', unsafe_allow_html=True)

col_intro1, col_intro2 = st.columns([4, 1])
with col_intro1:
    st.markdown(lorem) 
with col_intro2:
    st.image('assets/rap_jeu_logo.png', use_column_width=True)
#    st.markdown('''
#<img src="rap_jeu_logo.png">
#''', unsafe_allow_html=True)
#style="border-style:solid; border-color: rgba(170, 0, 245, 0.6); border-width: 1px;" 

artist_dict = get_artist_dict(sql_cnx)
album_dict = get_album_dict(sql_cnx)

print(len(album_dict))

artist_dict_rv = {i: k for k, i in artist_dict.items()}
artist_list = list(artist_dict_rv.keys())

default_value = 'Entre un artiste...'
col1, col2 =st.columns(2)
with col1:
    artist_1 = st.selectbox(label='', options=[default_value] + sorted(artist_list), key=1)
with col2:
    artist_2 = st.selectbox(label='', options=[default_value] + sorted(artist_list), key=2)

year_begin, year_end = st.slider('Période de recherche', 2000, 2021, (2000, 2021))
year_graph = get_graph_filter_by_years(G, year_begin, year_end)

search_button = st.button('Rechercher dans la base')
if artist_1 != default_value and artist_2 != default_value and search_button:

    if artist_1 == artist_2:
        st.error('Sélectionne deux artistes différents !')
 
    else:
        artist_id1 = artist_dict_rv[artist_1]
        artist_id2 = artist_dict_rv[artist_2]

        error = False
        try:
            shortest_path = nx.shortest_path(year_graph, artist_id1, artist_id2)

            shortest_path_edges =  [tuple((shortest_path[i], shortest_path[i+1])) for i in range(len(shortest_path) - 1)]
            album_ids = [year_graph.edges[edge]['album_id'] for edge in shortest_path_edges]

            condition = f'WHERE album_id = {album_ids[0]}' if len(album_ids) == 1 else f'WHERE album_id IN {tuple(album_ids)}'
            query = f'SELECT album_id, album_name, album_url, cover_url, release_year FROM album {condition}'
            album_featuring_table = query_to_dataframe(sql_cnx, query)
            album_featuring_table.set_index('album_id', inplace=True)

            query = f'SELECT artist_id, artist_name, artist_url FROM artist WHERE artist_id IN {tuple(shortest_path)}'
            artist_featuring_table = query_to_dataframe(sql_cnx, query)
            artist_featuring_table.set_index('artist_id', inplace=True)

            artist_names = [(artist_featuring_table.loc[artist_id1].artist_name, artist_featuring_table.loc[artist_id2].artist_name) for artist_id1, artist_id2 in shortest_path_edges]
            artist_urls = [(artist_featuring_table.loc[artist_id1].artist_url, artist_featuring_table.loc[artist_id2].artist_url) for artist_id1, artist_id2 in shortest_path_edges]

            album_cover_urls = [album_featuring_table.loc[album_id].cover_url for album_id in album_ids]
            album_names = [album_featuring_table.loc[album_id].album_name for album_id in album_ids]
            album_years = [album_featuring_table.loc[album_id].release_year.replace('NULL', '?') for album_id in album_ids]
            album_urls = [album_featuring_table.loc[album_id].album_url for album_id in album_ids]
            
            l = len(shortest_path_edges) - 1
            if l > 0:
                st.info(f'Nous avons trouvé {l} artistes pour connecter {artist_1.replace("$", "S")} à {artist_2.replace("$", "S")}.')
            else:
                st.info(f'Nous avons trouvé un featuring entre {artist_1.replace("$", "S")} et {artist_2.replace("$", "S")}.')
            
            col3, col4 = st.columns([1, 7])
            
            for i in range(len(shortest_path_edges)):
                with col3:
                    st.image(album_cover_urls[i], use_column_width=True)
                with col4:
                    st.markdown('''
<div style="background-color: rgba(85,26,139, 0.1); border-style:solid; border-color: rgba(85,26,139, 0.6); border-width: 1px; margin: 3px; margin-bottom: 13.5px; padding: 12px; border-radius: 5px">
<a href=%s>%s</a> en featuring avec <a href=%s>%s</a></b><br>Album : <a href=%s>%s<a/> (%s)
</div>
''' % (artist_urls[i][0], artist_names[i][0], artist_urls[i][1], artist_names[i][1], album_urls[i], album_names[i], album_years[i]), 
unsafe_allow_html=True) 

            with st.spinner('Génération du réseau de connection...'):
                graph_chart_data = get_graph_chart_data(G, artist_id1, artist_id2, artist_dict, album_dict)
                graph_chart_layout = get_graph_chart_layout()
                fig = go.Figure(data = graph_chart_data, layout = graph_chart_layout)

                st.plotly_chart(fig)

        except nx.exception.NetworkXNoPath:
            st.error('Nous ne trouvons pas de lien entre ces deux artistes sur cette période 🧐 ...')
            error = True

st.markdown('***')
st.markdown('''
<h3 style="font-family: 'Merriweather Sans', sans-serif; font-weight: Extra-bold; color: rgb(85,26,139);"><i>ANALYSE PAR ARTISTE</i></h1>
''', unsafe_allow_html=True)

artist_3 = st.selectbox(label='', options=[default_value] + sorted(artist_list), key=3)
if artist_3 != default_value:
    artist_id3 = artist_dict_rv[artist_3]
    artist_df = query_to_dataframe(sql_cnx, f'SELECT * FROM artist WHERE artist_id={artist_id3}').iloc[0]
    st.image(artist_df.picture_url)

st.markdown('***')
st.markdown('''
<h3 style="font-family: 'Merriweather Sans', sans-serif; font-weight: Extra-bold; color: rgb(85,26,139);"><i>A PROPOS</i></h1>
''', unsafe_allow_html=True)
st.markdown(lorem)
with st.expander('La base de données'):
    st.markdown(lorem)
st.markdown(lorem)
