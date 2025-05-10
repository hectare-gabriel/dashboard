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

# CSS para estilo minimalista com cores mais escuras
st.markdown("""
<style>
    /* Estilo dos popups */
    .leaflet-popup-content-wrapper {
        border-radius: 4px !important;
        box-shadow: 0 3px 6px rgba(0,0,0,0.16) !important;
        border: 1px solid #e0e0e0 !important;
    }
    .leaflet-popup-content {
        margin: 12px !important;
        font: 14px/1.5 'Segoe UI', Roboto, sans-serif !important;
        color: #333 !important;
    }
    .leaflet-popup-content p {
        margin: 8px 0 !important;
    }
    
    /* Estilo do filtro */
    .stMultiSelect [data-baseweb="tag"] {
        background-color: #e1e3e7 !important;
        border-radius: 6px !important;
        color: #2d3436 !important;
        font-weight: 500 !important;
    }
    .stMultiSelect [data-baseweb="select"] span {
        color: #2d3436 !important;
    }
    .stMultiSelect div[role="button"] {
        border-color: #b2bec3 !important;
    }
    
    /* Espaçamento */
    .filter-container {
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Título do dashboard
st.title("📌 Dashboard de Links - Região Metropolitana de São Paulo")

# Carregar dados
@st.cache_data
def load_data():
    df = pd.read_excel("map_dashboard/data/Base_teste.xlsx")
    # Preencher valores NaN/NULL nas colunas críticas
    df['Situação'] = df['Situação'].fillna('Não informado')
    df['Líder'] = df['Líder'].fillna('Não informado')
    df['Endereço'] = df['Endereço'].fillna('Não informado')
    return df

df = load_data()

# Converter vírgulas para pontos nas coordenadas e tratar valores inválidos
df['lat'] = pd.to_numeric(df['lat'].astype(str).str.replace(',', '.'), errors='coerce')
df['long'] = pd.to_numeric(df['long'].astype(str).str.replace(',', '.'), errors='coerce')

# Remover linhas com coordenadas inválidas (0,0 ou NaN)
df = df[(df['lat'] != 0) & (df['long'] != 0) & (df['lat'].notna()) & (df['long'].notna())]

# Container do filtro entre o título e o mapa
with st.container():
    st.markdown('<div class="filter-container">', unsafe_allow_html=True)
    situacoes = st.multiselect(
        "Filtrar por Situação do Link",
        options=df['Situação'].unique(),
        default=df['Situação'].unique(),
        key='situacao_filter'
    )
    st.markdown('</div>', unsafe_allow_html=True)

# Aplicar filtro
filtered_df = df[df['Situação'].isin(situacoes)]

# Mapa Interativo
st.subheader("Mapa de Localização dos Links")

# Centralizar o mapa em São Paulo (coordenadas aproximadas do centro da cidade)
map_center = [-23.5505, -46.6333]  # Latitude e Longitude de São Paulo

# Se houver dados filtrados, centralizar na média das coordenadas (mas manter zoom inicial)
if len(filtered_df) > 0:
    map_center = [filtered_df['lat'].mean(), filtered_df['long'].mean()]

# Mapa com estilo minimalista
m = folium.Map(
    location=map_center,
    zoom_start=12,
    tiles="CartoDB positron",
    control_scale=True,
    prefer_canvas=True,
    zoom_control=False
)

# Paleta de cores mais escuras
COLOR_SCHEME = {
    'Aberto - 85% Cheio (+3/5 pessoas)': {'color': '#1b5e20', 'icon': 'user-plus'},
    'Aberto - Tranquilo para receber mais': {'color': '#2e7d32', 'icon': 'user-plus'},
    'Fechado - não há espaço': {'color': '#c62828', 'icon': 'times'},
    'Fechado - Há espaço mas não consegue cuidar': {'color': '#d32f2f', 'icon': 'times-circle'},
    'Não informado': {'color': '#616161', 'icon': 'question'},
    'NA': {'color': '#616161', 'icon': 'question'}
}

# Adicionar marcadores com popups mais completos
for idx, row in filtered_df.iterrows():
    # Determinar o status baseado na situação
    situacao = str(row['Situação'])
    if 'Aberto' in situacao:
        status_key = next((k for k in COLOR_SCHEME.keys() if k in situacao), 'Aberto - Tranquilo para receber mais')
    elif 'Fechado' in situacao:
        status_key = next((k for k in COLOR_SCHEME.keys() if k in situacao), 'Fechado - Há espaço mas não consegue cuidar')
    else:
        status_key = 'Não informado'
    
    # Criar popup mais detalhado
    popup_content = f"""
    <div style='font-family: "Segoe UI", Roboto, sans-serif; font-size: 14px; line-height: 1.5;'>
        <h4 style='margin: 0 0 8px 0; color: {COLOR_SCHEME[status_key]['color']};'>{row['Líder']}</h4>
        <p style='margin: 4px 0;'><b>Endereço:</b> {row['Endereço']}</p>
        <p style='margin: 4px 0;'><b>Data/Horário:</b> {row['Data']} às {row['Horário']}</p>
        <p style='margin: 4px 0;'><b>Situação:</b> <span style='color: {COLOR_SCHEME[status_key]['color']}; 
        font-weight: 600;'>{row['Situação']}</span></p>
    </div>
    """
    
    folium.Marker(
        location=[row['lat'], row['long']],
        popup=folium.Popup(
            popup_content,
            max_width=300
        ),
        icon=folium.Icon(
            color=COLOR_SCHEME[status_key]['color'],
            icon=COLOR_SCHEME[status_key]['icon'],
            prefix='fa',
            icon_color='white'
        ),
        tooltip=f"{row['Líder']} - {row['Situação']}"
    ).add_to(m)

# Exibir mapa
st_folium(m, width=1200, height=600, returned_objects=[])

# Tabela de dados minimalista
st.subheader("Dados dos Links")

# Criar cópia do DataFrame para exibição (sem as colunas de coordenadas)
display_df = filtered_df.drop(columns=['lat', 'long']).copy()

# Garantir que todas as colunas tenham valores válidos para exibição
for col in display_df.columns:
    if display_df[col].dtype == 'object':
        display_df[col] = display_df[col].fillna('Não informado')

st.dataframe(
    display_df,
    hide_index=True,
    use_container_width=True,
    column_config={
        "Líder": "Líder",
        "Endereço": "Endereço",
        "Situação": st.column_config.SelectboxColumn(
            "Situação",
            options=df['Situação'].unique().tolist()
        )
    }
)

# Estatísticas
st.divider()
col1, col2, col3 = st.columns(3)
col1.metric(
    "Total de Links", 
    len(filtered_df),
    help="Quantidade total de links filtrados"
)
col2.metric(
    "Links Abertos", 
    len(filtered_df[filtered_df['Situação'].str.contains('Aberto', na=False)]),
    delta=f"{len(filtered_df[filtered_df['Situação'].str.contains('Aberto', na=False)])/len(filtered_df):.0%} do total",
    delta_color="off"
)
col3.metric(
    "Links Fechados", 
    len(filtered_df[filtered_df['Situação'].str.contains('Fechado', na=False)]),
    delta=f"{len(filtered_df[filtered_df['Situação'].str.contains('Fechado', na=False)])/len(filtered_df):.0%} do total",
    delta_color="off"
)