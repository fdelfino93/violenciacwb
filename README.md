# 📊 Análise de Homicídios em Curitiba — Dashboard Interativo

<p align="center">
  <img src="https://media.giphy.com/media/fQZX2aoRC1Tqw/giphy.gif" width="400" alt="Dashboard Animation">
</p>

---

## 📝 Descrição do Projeto
Este projeto oferece um **dashboard interativo** para a **análise de crimes em Curitiba**, incluindo dados sobre **Lesão Corporal, Homicídio Doloso, Feminicídio e Latrocínio**. Construído com **Streamlit** e **Plotly Express**, o painel permite uma exploração detalhada dos dados por meio de filtros dinâmicos e visualizações ricas.

---

## 🎯 Objetivo do Projeto
- **Centralizar e padronizar** dados de diferentes tipos de crimes.
- Permitir **filtros dinâmicos** por tipo de crime e bairro.
- Visualizar a **distribuição de crimes** em um mapa coroplético interativo de Curitiba.
- Analisar a **evolução mensal** dos crimes.
- Identificar os **bairros com maiores ocorrências** através de rankings (Top 10).
- Comparar o desempenho dos bairros com **gráficos e heatmaps**.

---

## 🎥 Demonstração do Projeto

Abaixo estão algumas capturas de tela do painel em ação:

<p align="center">
  <em>Gráfico de linha comparando a evolução mensal dos crimes.</em>
  <img src="./assets/graficoum.png" width="800" alt="Gráfico de evolução mensal dos crimes">
</p>

<p align="center">
  <em>Mapa de calor coroplético mostrando a distribuição de crimes por bairro.</em>
  <img src="./assets/mapacalor.png" width="800" alt="Mapa de calor de crimes por bairro">
</p>

---

## 🛠️ Tecnologias Utilizadas

| Ferramenta     | Descrição                               |
|---------------|-----------------------------------------|
| **Python**    | Linguagem principal do projeto          |
| **Streamlit** | Framework para criação de dashboards    |
| **Pandas**    | Manipulação e análise de dados          |
| **Plotly**    | Criação de gráficos interativos         |
| **Geopandas** | Leitura e manipulação de dados geoespaciais |
| **Unicodedata**| Normalização de texto (remover acentos) |

---

## 📂 Estrutura do Projeto

.
├── Corporal.csv
├── Doloso.csv
├── Feminicidio.csv
├── Latrocinio.csv
├── DIVISA_DE_BAIRROS.shp (e arquivos relacionados)
├── dataset.py            # Código principal do dashboard
├── requirements.txt      # Dependências do projeto
└── README.md             # Documentação do projeto


## 🚀 Como Rodar o Projeto

### 1️⃣ **Clone o repositório**
```bash
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio
```

### 2️⃣ **Instale as dependências**
Crie um ambiente virtual e instale as bibliotecas necessárias:
```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3️⃣ **Execute o dashboard**
```bash
streamlit run dataset.py
```