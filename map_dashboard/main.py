import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Links - RMSP",
    page_icon="📍",
    layout="wide"
)

# CSS para estilo minimalista
st.markdown("""
<style>
    /* Estilo dos popups */
    .leaflet-popup-content-wrapper {
        border-radius: 2px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        border: 1px solid #e0e0e0 !important;
    }
    .leaflet-popup-content {
        margin: 10px !important;
        font: 13px/1.4 'Segoe UI', Roboto, sans-serif !important;
        color: #333 !important;
    }
    
    /* Sidebar minimalista */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa !important;
    }
    .stMultiSelect [data-baseweb="tag"] {
        background-color: #f1f3f4 !important;
        border-radius: 4px !important;
    }
</style>
""", unsafe_allow_html=True)

# Título do dashboard
st.title("📌 Dashboard de Links - Região Metropolitana de São Paulo")

# Carregar dados
@st.cache_data
def load_data():
    return pd.read_excel("map_dashboard/data/Base_teste.xlsx")

df = load_data()

# Converter vírgulas para pontos nas coordenadas
df['lat'] = df['lat'].astype(str).str.replace(',', '.').astype(float)
df['long'] = df['long'].astype(str).str.replace(',', '.').astype(float)

# Sidebar - Filtros
st.sidebar.header("Filtros")
situacoes = st.sidebar.multiselect(
    "Situação do Link",
    options=df['Situação'].unique(),
    default=df['Situação'].unique(),
    key='situacao_filter'
)

lideres = st.sidebar.multiselect(
    "Líderes",
    options=df['Lider'].unique(),
    default=df['Lider'].unique(),
    key='lider_filter'
)

# Aplicar filtros
filtered_df = df[
    (df['Situação'].isin(situacoes)) &
    (df['Lider'].isin(lideres))
]

# Mapa Interativo
st.subheader("Mapa de Localização dos Links")

# Centralizar o mapa
map_center = [filtered_df['lat'].mean(), filtered_df['long'].mean()]

# Mapa com estilo minimalista
m = folium.Map(
    location=map_center,
    zoom_start=12,
    tiles="CartoDB positron",  # Estilo clean
    control_scale=True,
    prefer_canvas=True,
    zoom_control=False  # Remove controles de zoom para mais minimalismo
)

# Paleta de cores minimalista
COLOR_SCHEME = {
    'Aberto': {'color': '#2e7d32', 'icon': 'circle'},  # Verde escuro
    'Fechado': {'color': '#c62828', 'icon': 'times'}   # Vermelho escuro
}

# Adicionar marcadores clean
for idx, row in filtered_df.iterrows():
    status = row['Situação']
    
    folium.Marker(
        location=[row['lat'], row['long']],
        popup=folium.Popup(
            f"""<div style='font-family: "Segoe UI", Roboto, sans-serif; font-size: 13px'>
                <p style='margin-bottom: 4px;'><b>Líder:</b> {row['Lider']}</p>
                <p style='margin-bottom: 4px;'><b>Status:</b> 
                <span style='color:{COLOR_SCHEME[status]['color']}; font-weight: 500;'>
                {status}</span></p>
                <p style='margin: 0;'><b>Local:</b> {row['Endereco'].split(',')[0]}</p>
                </div>""",
            max_width=250
        ),
        icon=folium.Icon(
            color=COLOR_SCHEME[status]['color'],
            icon=COLOR_SCHEME[status]['icon'],
            prefix='fa',
            icon_color='white'  # Ícones brancos para melhor contraste
        )
    ).add_to(m)

# Exibir mapa
st_folium(m, width=1200, height=600, returned_objects=[])

# Tabela de dados minimalista
st.subheader("Dados dos Links")
st.dataframe(
    filtered_df.drop(columns=['lat', 'long']),
    hide_index=True,
    use_container_width=True,
    column_config={
        "Lider": "Líder",
        "Auxiliar": "Auxiliar",
        "Endereco": "Endereço",
        "Situação": st.column_config.SelectboxColumn(
            "Situação",
            options=["Aberto", "Fechado"]
        )
    }
)

# Estatísticas clean
st.divider()
col1, col2 = st.columns(2)
col1.metric(
    "Total de Links", 
    len(filtered_df),
    help="Quantidade total de links filtrados"
)
col2.metric(
    "Links Abertos", 
    len(filtered_df[filtered_df['Situação'] == 'Aberto']),
    delta=f"{len(filtered_df[filtered_df['Situação'] == 'Aberto'])/len(filtered_df):.0%} do total",
    delta_color="off"
)