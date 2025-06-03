import streamlit as st
import json
import datetime
import os
import matplotlib.pyplot as plt
from collections import defaultdict

# Configurações de arquivo
STORAGE_PATH = "."
ARQUIVO_ALIMENTOS = os.path.join(STORAGE_PATH, "alimentos.json")

# Funções de persistência de dados
def carregar_alimentos():
    """Carrega a lista de alimentos do arquivo JSON com verificação de estrutura"""
    if os.path.exists(ARQUIVO_ALIMENTOS):
        try:
            with open(ARQUIVO_ALIMENTOS, "r", encoding="utf-8") as f:
                alimentos = json.load(f)
                
                # Verifica a estrutura de cada item
                alimentos_validos = []
                for item in alimentos:
                    if isinstance(item, dict) and "nome" in item:
                        # Aceita tanto "calorias_p100g" quanto "calorias"
                        calorias = item.get("calorias_p100g", item.get("calorias"))
                        if calorias is None:
                            st.error(f"Item sem informação de calorias: {item}")
                            continue
                            
                        alimentos_validos.append({
                            "nome": item["nome"],
                            "calorias_p100g": float(calorias),
                            "porcao": item.get("porcao", "100g")
                        })
                    else:
                        st.error(f"Item inválido ignorado: {item}")
                
                return alimentos_validos
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            st.error(f"Erro ao ler arquivo: {str(e)}")
            return []
    return []

def salvar_alimentos(alimentos):
    """Salva a lista de alimentos no arquivo JSON"""
    with open(ARQUIVO_ALIMENTOS, "w", encoding="utf-8") as f:
        json.dump(alimentos, f, indent=2, ensure_ascii=False)

def registrar_refeicao(usuario, data, refeicao, alimento, quantidade, calorias):
    """Registra uma refeição no histórico do usuário"""
    path = f"historico_{usuario.lower()}.txt"
    registro = f"{data}|{refeicao}|{alimento}|{quantidade}|{calorias}\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(registro)

def carregar_historico(usuario):
    """Carrega o histórico de refeições do usuário"""
    path = f"historico_{usuario.lower()}.txt"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return [linha.strip().split("|") for linha in f.readlines()]
    return []

def registrar_peso(usuario, data, peso):
    """Registra o peso do usuário"""
    path = f"peso_{usuario.lower()}.txt"
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"{data}|{peso}\n")

def carregar_pesos(usuario):
    """Carrega o histórico de pesos do usuário"""
    path = f"peso_{usuario.lower()}.txt"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return [linha.strip().split("|") for linha in f.readlines()]
    return []

# Inicialização dos dados
if not os.path.exists(ARQUIVO_ALIMENTOS):
    salvar_alimentos([])

alimentos = carregar_alimentos()
alimentos_dict = {item["nome"]: item["calorias_p100g"] for item in alimentos}

# Configuração da página
st.set_page_config(layout="wide")
st.title("📊 Sistema de Acompanhamento Alimentar e de IMC")

# Sidebar - Perfil do usuário
st.sidebar.header("👤 Perfil")
usuario = st.sidebar.selectbox("Selecione o usuário", ["Milena", "Raul"])
peso = st.sidebar.number_input("Peso (kg)", min_value=30.0, max_value=200.0, step=0.1, value=65.0)
altura = st.sidebar.number_input("Altura (cm)", min_value=120.0, max_value=250.0, step=0.1, value=165.0)

# Cálculo de água recomendada
agua_ml = peso * 35
litros = agua_ml / 1000
copos = round(litros / 0.25)
st.sidebar.markdown(f"**🍼 Água recomendada:** {litros:.1f} L (~{copos} copos de 250ml)")

# Cálculo de IMC
if altura > 0:
    imc = peso / ((altura/100) ** 2)
    st.sidebar.markdown(f"**🏋️ IMC Atual:** {imc:.1f}")
    if imc < 18.5:
        st.sidebar.warning("Classificação: Abaixo do peso")
    elif 18.5 <= imc < 25:
        st.sidebar.success("Classificação: Peso normal")
    elif 25 <= imc < 30:
        st.sidebar.warning("Classificação: Sobrepeso")
    else:
        st.sidebar.error("Classificação: Obesidade")

# Abas principais
tabs = st.tabs(["Refeições", "Histórico", "Cadastrar Alimento", "Peso & IMC"])

# Aba 1: Refeições
with tabs[0]:
    st.header(f"🍎 Registrar Refeição para {usuario}")
    
    col1, col2 = st.columns(2)
    with col1:
        data = st.date_input("Data", value=datetime.date.today())
        refeicao = st.selectbox("Refeição", ["Café da Manhã", "Lanche", "Almoço", "Lanche da Tarde", "Jantar"])
    
    with col2:
        alimento_escolhido = st.selectbox("Alimento", list(alimentos_dict.keys()))
        quantidade_g = st.number_input("Quantidade (g)", min_value=1.0, step=1.0, value=100.0)
    
    if st.button("Registrar Refeição", key="registrar_refeicao"):
        calorias_p100 = alimentos_dict[alimento_escolhido]
        calorias = (calorias_p100 / 100) * quantidade_g
        registrar_refeicao(
            usuario=usuario,
            data=data.isoformat(),
            refeicao=refeicao,
            alimento=alimento_escolhido,
            quantidade=quantidade_g,
            calorias=calorias
        )
        st.success(f"Refeição registrada! {quantidade_g}g de {alimento_escolhido} = {calorias:.1f} kcal")

# Aba 2: Histórico
with tabs[1]:
    st.header(f"📅 Histórico de Refeições - {usuario}")
    
    historico = carregar_historico(usuario)
    
    if historico:
        # Agrupar refeições por dia
        dias = defaultdict(list)
        for data, refeicao, alimento, quantidade, calorias in historico:
            dias[data].append({
                "refeicao": refeicao,
                "alimento": alimento,
                "quantidade": quantidade,
                "calorias": float(calorias)
            })
        
        # Ordenar dias por data (mais recente primeiro)
        dias_ordenados = sorted(dias.items(), key=lambda x: x[0], reverse=True)
        
        # Seletor de data
        datas_disponiveis = [data for data, _ in dias_ordenados]
        data_selecionada = st.selectbox(
            "Selecione o dia para visualizar:",
            options=datas_disponiveis,
            index=0
        )
        
        # Mostrar todas as refeições do dia selecionado em cards
        st.subheader(f"Refeições em {data_selecionada}")
        total_dia = sum(ref["calorias"] for ref in dias[data_selecionada])
        st.metric("Total do dia", f"{total_dia:.1f} kcal")
        
        # Dividir refeições em colunas
        cols = st.columns(2)
        col_idx = 0
        
        for refeicao in dias[data_selecionada]:
            with cols[col_idx]:
                with st.container(border=True):
                    st.markdown(f"#### 🍽️ {refeicao['refeicao']}")
                    st.markdown(f"**🍲 {refeicao['alimento']}**")
                    st.markdown(f"🔹 **Quantidade:** {refeicao['quantidade']}g")
                    st.markdown(f"🔥 **Calorias:** {refeicao['calorias']:.1f} kcal")
            
            # Alternar entre colunas
            col_idx = 1 - col_idx
        
        # Opção para mostrar todas as refeições
        if st.checkbox("Mostrar histórico completo"):
            st.subheader("Histórico Completo")
            for data, refeicoes in dias_ordenados:
                with st.expander(f"📅 {data} - Total: {sum(r['calorias'] for r in refeicoes):.1f} kcal"):
                    for ref in refeicoes:
                        with st.container(border=True):
                            st.markdown(f"**{ref['refeicao']}**: {ref['alimento']} ({ref['quantidade']}g) - {ref['calorias']:.1f} kcal")
    else:
        st.info("Nenhum histórico registrado.")

# Aba 3: Cadastrar Alimento
with tabs[2]:
    st.header("🌟 Cadastrar Novo Alimento")
    
    with st.form("form_alimento", clear_on_submit=True):
        nome = st.text_input("Nome do alimento*", help="Ex: Maçã, Arroz integral")
        calorias_p100g = st.number_input("Calorias por 100g*", min_value=0.0, step=1.0, value=100.0)
        porcao = st.text_input("Porção de referência", value="100g", help="Ex: 1 unidade, 1 colher de sopa")
        
        submitted = st.form_submit_button("Cadastrar Alimento")
        if submitted:
            if nome.strip() and calorias_p100g >= 0:
                novo_alimento = {
                    "nome": nome.strip(),
                    "calorias_p100g": float(calorias_p100g),
                    "porcao": porcao.strip() if porcao.strip() else "100g"
                }
                
                # Verifica se já existe
                if any(a["nome"].lower() == novo_alimento["nome"].lower() for a in alimentos):
                    st.warning("Este alimento já está cadastrado!")
                else:
                    alimentos.append(novo_alimento)
                    salvar_alimentos(alimentos)
                    alimentos_dict[nome] = calorias_p100g
                    st.success(f"'{nome}' cadastrado com sucesso!")
                    st.experimental_rerun()
            else:
                st.error("Preencha os campos obrigatórios (*)")

# Aba 4: Peso & IMC
with tabs[3]:
    st.header(f"📈 Evolução do Peso e IMC - {usuario}")
    
    col1, col2 = st.columns(2)
    with col1:
        peso_hoje = st.number_input("Registrar peso atual (kg)", min_value=30.0, max_value=200.0, step=0.1, value=peso)
        if st.button("Salvar Peso"):
            registrar_peso(usuario, datetime.date.today().isoformat(), peso_hoje)
            st.success("Peso registrado com sucesso!")
            st.experimental_rerun()
    
    # Gráfico de evolução
    historico_peso = carregar_pesos(usuario)
    if historico_peso:
        # Ordenar por data
        historico_peso.sort(key=lambda x: x[0])
        
        datas = [item[0] for item in historico_peso]
        pesos = [float(item[1]) for item in historico_peso]
        alturas_m = altura / 100
        imcs = [p / (alturas_m ** 2) for p in pesos]
        
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(datas, pesos, 'b-o', label="Peso (kg)")
        ax.set_xlabel("Data")
        ax.set_ylabel("Peso (kg)", color='b')
        ax.tick_params(axis='y', labelcolor='b')
        
        ax2 = ax.twinx()
        ax2.plot(datas, imcs, 'r-s', label="IMC")
        ax2.set_ylabel("IMC", color='r')
        ax2.tick_params(axis='y', labelcolor='r')
        
        ax.set_title(f"Evolução de Peso e IMC - {usuario}")
        ax.set_xticklabels(datas, rotation=45)
        fig.tight_layout()
        st.pyplot(fig)
        
        # Mostrar últimos registros
        st.subheader("Últimos Registros")
        cols = st.columns(3)
        for i, (data, peso_reg) in enumerate(historico_peso[-5:]):  # Mostrar últimos 5 registros
            with cols[i % 3]:
                st.metric(label=data, value=f"{float(peso_reg):.1f} kg")
    else:
        st.info("Nenhum registro de peso encontrado.")

# Rodapé
st.markdown("---")
st.caption("Sistema de Acompanhamento Alimentar e de IMC - Desenvolvido para Milena e Raul")