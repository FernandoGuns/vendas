# -*- coding: utf-8 -*-
import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

# Leitura das bases de vendas
vendas_2020 = pd.read_excel("Base Vendas - 2020.xlsx")
vendas_2021 = pd.read_excel("Base Vendas - 2021.xlsx")
vendas_2022 = pd.read_excel("Base Vendas - 2022.xlsx")

colunas_padrao = ["Data da Venda", "Ordem de Compra", "ID Produto", "ID Cliente", "Qtd Vendida", "ID Loja"]
vendas_2020.columns = colunas_padrao
vendas_2021.columns = colunas_padrao
vendas_2022.columns = colunas_padrao

vendas = pd.concat([vendas_2020, vendas_2021, vendas_2022], ignore_index=True)

# Leitura dos cadastros
produtos = pd.read_excel("Cadastro Produtos.xlsx")
lojas = pd.read_excel("Cadastro Lojas.xlsx")

# Renomeando SKU para ID Produto
if 'SKU' in produtos.columns:
    produtos.rename(columns={'SKU': 'ID Produto'}, inplace=True)
if 'SKU' in vendas.columns:
    vendas.rename(columns={'SKU': 'ID Produto'}, inplace=True)

# Convertendo datas
vendas["Data da Venda"] = pd.to_datetime(vendas["Data da Venda"], dayfirst=True)

# Merge das tabelas
base = vendas.merge(produtos, on="ID Produto", how="left")
base = base.merge(lojas, on="ID Loja", how="left")

# Colunas auxiliares
base["Ano"] = base["Data da Venda"].dt.year
base["Valor da Venda"] = base["Qtd Vendida"] * base["Preço Unitario"]

# Filtros únicos
filtros = {
    "produto": base["Produto"].dropna().unique(),
    "loja": base["Nome da Loja"].dropna().unique(),
    "marca": base["Marca"].dropna().unique(),
    "tipo": base["Tipo do Produto"].dropna().unique(),
}

# App Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])
server = app.server

app.layout = dbc.Container([
    html.H1("📊 Dashboard de Vendas", className="text-center my-4"),

    dbc.Row([
        dbc.Col(dcc.Dropdown(id='filtro_tipo', options=[{'label': i, 'value': i} for i in filtros['tipo']],
                             placeholder="Selecione o Tipo de Produto"), md=4),
        dbc.Col(dcc.Dropdown(id='filtro_marca', placeholder="Selecione a Marca"), md=4),
        dbc.Col(dcc.Dropdown(id='filtro_produto', options=[{'label': i, 'value': i} for i in filtros['produto']],
                             multi=True, placeholder="Filtrar por Produto"), md=4),
        dbc.Col(dcc.Dropdown(id='filtro_loja', options=[{'label': i, 'value': i} for i in filtros['loja']],
                             multi=True, placeholder="Filtrar por Loja"), md=4),
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(dcc.Graph(id='grafico_ano'), md=6),
        dbc.Col(dcc.Graph(id='grafico_produto'), md=6),
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='grafico_loja'), md=6),
        dbc.Col(dcc.Graph(id='grafico_pizza_tipo'), md=6),
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='grafico_area_tempo'), md=12),
    ]),
], fluid=True)

@app.callback(
    Output('filtro_marca', 'options'),
    Input('filtro_tipo', 'value')
)
def atualizar_marcas(tipo):
    if tipo:
        marcas = base[base['Tipo do Produto'] == tipo]['Marca'].dropna().unique()
        return [{'label': m, 'value': m} for m in marcas]
    return []

@app.callback(
    [Output('grafico_ano', 'figure'),
     Output('grafico_produto', 'figure'),
     Output('grafico_loja', 'figure'),
     Output('grafico_pizza_tipo', 'figure'),
     Output('grafico_area_tempo', 'figure')],
    [Input('filtro_tipo', 'value'),
     Input('filtro_marca', 'value'),
     Input('filtro_produto', 'value'),
     Input('filtro_loja', 'value')]
)
def atualizar_graficos(tipo, marca, produtos, lojas):
    df = base.copy()
    if tipo:
        df = df[df['Tipo do Produto'] == tipo]
    if marca:
        df = df[df['Marca'] == marca]
    if produtos:
        df = df[df['Produto'].isin(produtos)]
    if lojas:
        df = df[df['Nome da Loja'].isin(lojas)]

    df['Mês'] = df['Data da Venda'].dt.to_period("M").astype(str)

    fig1 = px.bar(df.groupby("Ano")["Valor da Venda"].sum().reset_index(),
                  x="Ano", y="Valor da Venda", title="Vendas por Ano",
                  color_discrete_sequence=["#00BFFF"], template='plotly_dark')

    fig2 = px.bar(df.groupby("Produto")["Valor da Venda"].sum().nlargest(10).reset_index(),
                  x="Valor da Venda", y="Produto", orientation='h',
                  title="Top 10 Produtos", color_discrete_sequence=["#FF7F50"], template='plotly_dark')

    fig3 = px.bar(df.groupby("Nome da Loja")["Valor da Venda"].sum().reset_index(),
                  x="Nome da Loja", y="Valor da Venda", title="Vendas por Loja",
                  color_discrete_sequence=["#FFD700"], template='plotly_dark')

    fig4 = px.pie(df, names="Tipo do Produto", values="Valor da Venda", title="Distribuição por Tipo de Produto",
                  color_discrete_sequence=px.colors.qualitative.Set3, template='plotly_dark')

    fig5 = px.area(df.groupby("Mês")["Valor da Venda"].sum().reset_index(),
                   x="Mês", y="Valor da Venda", title="Evolução Mensal de Vendas",
                   color_discrete_sequence=["#1E90FF"], template='plotly_dark')

    return fig1, fig2, fig3, fig4, fig5

if __name__ == '__main__':
    app.run(debug=True)
