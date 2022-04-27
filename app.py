from functions import *
import base64, joblib, os

# CONFIG

st.set_page_config(
     page_title='Roland Gamos',
     page_icon='🎾',
     layout='centered',
     initial_sidebar_state='expanded',
     menu_items={
         'Report a bug': 'https://github.com/leoguillaume/roland-gamos-app/issues',
         'Get help': None,
         'About': '''Application réalisée par Léo Guillaume ([Github](https://github.com/leoguillaume) - [Twitter](https://twitter.com/leoguillaume) - [Linkedin](https://www.linkedin.com/in/leoguillaume/)).'''

     }
)

INPUT_PATH = 'inputs'
GRAPH_NAME = 'graph.p'
ASSET_PATH = 'assets'
FIRST_YEAR = 2000
LAST_YEAR = 2021
START_TIME = 1543
SQL_CNX = psycopg2.connect(host='localhost', database='rapdashboard', user='leo')
G = joblib.load(os.path.join(INPUT_PATH, GRAPH_NAME))
ALBUM_DICT = get_album_dict(SQL_CNX)
ARTIST_DICT = get_artist_dict(SQL_CNX)
ARTIST_DICT_R = {i: k for k, i in ARTIST_DICT.items()}
ARTIST_LIST = list(ARTIST_DICT_R.keys())
DEFAULT_VALUE = 'Entre un artiste...'

# MAIN

## INTRO

with st.container():

    st.markdown('''
<style>
@import url('https://fonts.googleapis.com/css2?family=Merriweather+Sans:ital,wght@1,800&display=swap');
</style>
<h1 style="font-family: 'Merriweather Sans', sans-serif; font-weight: Extra-bold; color: rgb(85,26,139); font-size: 64px;"><i>LE ROLAND GAMOS</i></h1>
''', unsafe_allow_html=True)
    #col1, col2 = st.columns([4, 1])
    #with col1:
    st.markdown(f'''
<div align="justify">
Bienvenue sur l'application du jeu du Roland Gamos inspiré de l'emission Rap Jeu produite par Red Bull Binks. Cette application permet grâce à des graphes en réseau de visualiser comment les connections entre les artistes du rap français et leur communautés.
''', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 6, 1])
    with col2:
        st.image(os.path.join(ASSET_PATH, 'intro.png'), use_column_width=True)
#<img width='200' height='100' src='data:image/png;base64, {base64.b64encode(open(os.path.join(ASSET_PATH, 'graph.png'), 'rb').read()).decode()}' style=width: 60%; display: block;margin-left: auto; margin-right: auto;'>
    st.markdown(f'''
<h3>Règles du jeu</h3>
Le but étant de partir d'un.e artiste du rap game et de trouver à tout de rôle un autre artiste qui a fait un featuring avec le précédent cité. 
Mais une démonstration vaut mieux que mille explications, voici une des joutes les plus mémorables de l'emission :
<br><br>
</div>
''', unsafe_allow_html=True)
    #with col2:
    #    st.markdown(f'''
#<div class='logo'>
#    <img class='logo-img' width='150' height='150' src='data:image/png;base64, {base64.b64encode(open(os.path.join(ASSET_PATH, 'rap_jeu_logo.png'), 'rb').read()).decode()}' style='border-style: solid; border-color: rgb(85,26,139); border-width: 2px; border-radius: 100px;'>
#    <p class='logo-text'></p>
#</div>
#''', unsafe_allow_html=True)

st.video('https://www.youtube.com/watch?v=ihGqtHBIOEQ', start_time=START_TIME)

## FEATURINGS

with st.container():

    st.markdown('''<h3>Fonctionalités</h3>
🎤 <b>[ Recherche ]</b> Sélectionne 2 artistes dans les listes déroulantes.<br>
⏳ <b>[ Période ]</b> A l'aide du curseur tu peux réstreindre la période de recherche, les communautés d'artistes évoluent avec le temps !<br>
🔍 <b>[ Zoom]</b> Zoom dans le graphe en sélectionnant une zone pour explorer les connections.<br>

''', unsafe_allow_html=True)

    col1, col2 =st.columns(2)
    with col1:
        artist_1 = st.selectbox(label='', options=[DEFAULT_VALUE] + sorted(ARTIST_LIST), key=1)
    with col2:
        artist_2 = st.selectbox(label='', options=[DEFAULT_VALUE] + sorted(ARTIST_LIST), key=2)
    
    year_begin, year_end = st.slider('Période de recherche', FIRST_YEAR, LAST_YEAR, (FIRST_YEAR, LAST_YEAR), key=3)
    if year_begin != FIRST_YEAR or year_end != LAST_YEAR:
        year_graph = get_graph_filter_by_years(G, year_begin, year_end)
    else:
        year_graph = G.copy()
    search = st.button('Rechercher dans la base', key=4)
    if search and artist_1 != DEFAULT_VALUE and artist_2 != DEFAULT_VALUE:
        if artist_1 == artist_2:
            st.error('Sélectionne deux artistes différents !')
 
        else:
            artist_1_id = ARTIST_DICT_R[artist_1]
            artist_2_id = ARTIST_DICT_R[artist_2]

            try:
                
                shortest_path = nx.shortest_path(year_graph, artist_1_id, artist_2_id)
                shortest_path_edges = [tuple((shortest_path[i], shortest_path[i+1])) for i in range(len(shortest_path) - 1)]
                album_ids = [year_graph.edges[edge]['album_id'] for edge in shortest_path_edges]
                album_ids_explode = [str(album_id) for album_id_list in album_ids for album_id in album_id_list]

                query = f'SELECT album_id, album_name, album_url, cover_url, release_year FROM album WHERE album_id IN ({", ".join(album_ids_explode)})'     
                album_featuring_table = query_to_dataframe(SQL_CNX, query)
                album_featuring_table.set_index('album_id', inplace=True)

                query = f'SELECT artist_id, artist_name, artist_url FROM artist WHERE artist_id IN {tuple(shortest_path)}'
                artist_featuring_table = query_to_dataframe(SQL_CNX, query)
                artist_featuring_table.set_index('artist_id', inplace=True)

                for i, edge in enumerate(shortest_path_edges):

                    featuring_artist_1 = artist_featuring_table.loc[edge[0]].artist_name
                    featuring_artist_2 = artist_featuring_table.loc[edge[1]].artist_name
                    featuring_artist_1_url = artist_featuring_table.loc[edge[0]].artist_url
                    featuring_artist_2_url = artist_featuring_table.loc[edge[1]].artist_url

                    selected_years = set(str(year) for year in range(2000, 2022) if year >= year_begin and year <= year_end)
                    featuring_album_ids = [album_id for album_id in album_ids[i] if album_featuring_table.loc[album_id].release_year in selected_years]
                    featuring_album_years = [album_featuring_table.loc[album_id].release_year for album_id in featuring_album_ids]
                    featuring_album_years = [int(year.replace('NULL', '100000')) for year in featuring_album_years]
                    featuring_album_ids = np.array(featuring_album_ids)[np.argsort(featuring_album_years)].tolist()
                    featuring_album_years.sort()
                    featuring_album_years = [str(year).replace('10000', '?') for year in featuring_album_years]
                    featuring_album_names = [album_featuring_table.loc[album_id].album_name for album_id in featuring_album_ids]
                    featuring_album_urls = [album_featuring_table.loc[album_id].album_url for album_id in featuring_album_ids]
                    featuring_cover_urls = [album_featuring_table.loc[album_id].cover_url for album_id in featuring_album_ids]

                    col1, col2 = st.columns([1, 7])

                    with col1:
                        st.image(featuring_cover_urls[0], use_column_width=True)
                        
                    with col2:
                        st.markdown(get_featuring_infos(featuring_artist_1, featuring_artist_2, featuring_artist_1_url, featuring_artist_2_url, featuring_album_names[0],  featuring_album_names[0],  featuring_album_years[0]), unsafe_allow_html=True)
                        if len(featuring_album_ids) > 1:
                            with st.expander(f'Egalement sur {len(featuring_album_ids) -1} autres albums.'):
                                    st.markdown(get_featuring_other_album_infos(featuring_album_names, featuring_album_urls, featuring_album_years), unsafe_allow_html=True)    
                
                with st.spinner('Génération du réseau de connection...'):
                    st.write('💡 Plus les artistes ont collaboré entre eux, plus ils sont proches !')
                    fig = get_featuring_graph_chart(year_graph, artist_1_id, artist_2_id, ARTIST_DICT)
                    st.plotly_chart(fig)

            except nx.exception.NetworkXNoPath:
                 st.error('Nous ne trouvons pas de lien entre ces deux artistes sur cette période 🧐')

## ARTIST

with st.container():

    st.markdown('''***
<h2 style="font-family: 'Merriweather Sans', sans-serif; font-weight: Extra-bold; color: rgb(85,26,139);"><i>ANALYSE UN ARTISTE</i></h2>
'''
, unsafe_allow_html=True)
    artist = st.selectbox(label='', options=[DEFAULT_VALUE] + sorted(ARTIST_LIST), key=5)
    search = st.button('Rechercher dans la base', key=6)

    if search and artist != DEFAULT_VALUE:

        artist_id = ARTIST_DICT_R[artist]
        artist_graph = get_artist_graph(G, artist_id)
        artist_years = sorted(list(set(int(y)  for n, d in artist_graph[artist_id].items() for y in d['release_year'] if y != 'NULL')))
        
        artist_data = query_to_dataframe(SQL_CNX, f'SELECT * FROM artist WHERE artist_id = {artist_id}').iloc[0]
        col1, col2 = st.columns([2, 6])

        with col1:
            if artist_data.picture_url != 'NULL':
                st.image(artist_data.picture_url, use_column_width=True)
            else:
                st.image('https://assets.genius.com/images/default_avatar_300.png?1646171540', use_column_width=True)
        
        with col2:
            text = f'''
    <div style="background-color: rgba(85,26,139, 0.1); border-style:solid; border-color: rgba(85,26,139, 0.6); border-width: 1px; margin: 3px; margin-bottom: 13.5px; padding: 12px; border-radius: 5px">
    Apparait en base de {artist_years[0]} à {artist_years[-1]}.
    '''

            if artist_data.instagram_url != 'NULL' or artist_data.twitter_url != 'NULL':
                text += f' Réseaux de l\'artiste :'
                if artist_data.instagram_url != 'NULL':
                    text += f'<li><a href="{artist_data.instagram_url}">Instagram</a></li>'
                if artist_data.twitter_url != 'NULL':
                    text += f'<li><a href="{artist_data.twitter_url}">Twitter</a></li>'

            text +='</div>'
            st.markdown(text, unsafe_allow_html=True)
       
        col1, col2, col3 = st.columns(3)
        with col1:
            query = f'SELECT COUNT(*) FROM artist_album WHERE artist_id = {artist_id}'
            album_count = get_query(SQL_CNX, query, all=False)[0]
            st.metric('Albums', album_count)
        with col2:
            featuring_count = 0
            for f in list(G[artist_id]):
                featuring_count += len(G[artist_id][f]['release_year'])
            st.metric('Featurings', featuring_count)
        with col3:
            st.metric('Connections', nx.degree(G)[artist_id])
        fig = get_artist_graph_chart(artist_graph, artist_id, ARTIST_DICT)
        st.plotly_chart(fig)



## ABOUT

with st.container():

    st.markdown('''***
<h3 style="font-family: 'Merriweather Sans', sans-serif; font-weight: Extra-bold; color: rgb(85,26,139);"><i>A PROPOS</i></h1>
''', unsafe_allow_html=True)    
    st.markdown("La base de données est issue d'un long processus de recherche automatisée de données musicales sur [Genius](https://genius.com/) et les connections entre les artistes sont établies grâce à la théorie des graphes.")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📀 Nombre d'albums", len(ARTIST_DICT))
    with col2:
        st.metric("🎤 Nombre d'artistes", len(ALBUM_DICT))
    with col3:
        st.metric("🤝 Nombre de connections", G.number_of_edges())

    st.markdown("Je m'appelle Léo Guillaume, je suis data scientist et passionné de rap. Vous pouvez retrouver le code de cette application sur mon [GitHub](https://github.com/leoguillaume/roland-gamos-app) et n'hésitez pas à me suivre sur [Twitter](https://twitter.com/leo_guillaume__) et sur [LinkedIn](https://www.linkedin.com/in/leoguillaume/), tous vos feedbacks sont les bienvenues !")
