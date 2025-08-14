# app.py — MVP Sistema de Gestão Escolar
# AUTOR: Pedro / Gemini (Versão Corrigida)
import os
import sqlite3
from contextlib import closing
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

DB_PATH = "escola.db"

# -------------------- Utilidades de Banco -------------------- #

def get_conn():
    # check_same_thread=False é necessário para o Streamlit
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    try:
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        with closing(get_conn()) as conn:
            with open(schema_path, encoding="utf-8") as f:
                schema_sql = f.read()
            conn.executescript(schema_sql)
        st.success("Banco de dados inicializado com sucesso!")
    except Exception as e:
        st.error(f"Erro ao inicializar o banco de dados: {e}")

# O decorator @st.cache_data melhora a performance, guardando o resultado de funções
@st.cache_data(show_spinner="Consultando dados...")
def get_df(sql: str, params: tuple | list = ()):
    with closing(get_conn()) as conn:
        return pd.read_sql(sql, conn, params=params)

def execute(sql: str, params: tuple | list = ()):
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        return cur.lastrowid

# -------------------- UI Base -------------------- #

st.set_page_config(page_title="Gestão Escolar — MVP", layout="wide")
st.title("📚 Sistema de Gestão Escolar — MVP")

with st.sidebar:
    st.header("🔐 Perfil de acesso (simples)")
    perfil = st.radio(
        "Escolha seu perfil",
        options=["Gestor", "Professor", "Responsável"],
        index=0,  # Gestor por padrão
    )
    st.divider()
    if st.button("🚨 Inicializar/Resetar Banco de Dados 🚨"):
        init_db()
    st.caption(f"Banco de dados: {DB_PATH}")

# --- Abas principais da aplicação ---
abas = st.tabs([
    "🏠 Dashboard",
    "📝 Notas & Atividades",
    "✅ Frequência",
    "📣 Comunicação",
    "⚙️ Cadastros básicos",
])

# -------------------- Dashboard -------------------- #
with abas[0]:
    # <--- CORREÇÃO: Nomes das tabelas atualizados
    total_alunos = get_df("SELECT COUNT(*) c FROM Alunos")["c"].iat[0]
    total_turmas = get_df("SELECT COUNT(*) c FROM Turmas")["c"].iat[0]
    total_disciplinas = get_df("SELECT COUNT(*) c FROM Disciplinas")["c"].iat[0]
    total_avisos = get_df("SELECT COUNT(*) c FROM Avisos")["c"].iat[0]

    colA, colB, colC, colD = st.columns(4)
    colA.metric("Alunos", total_alunos)
    colB.metric("Turmas", total_turmas)
    colC.metric("Disciplinas", total_disciplinas)
    colD.metric("Avisos", total_avisos)

    st.subheader("Rendimento — distribuição de notas")
    
    # <--- CORREÇÃO: Consulta de notas totalmente reescrita para o novo schema
    df_notas = get_df(
        """
        SELECT 
            n.id_nota, 
            a.nome_completo AS aluno, 
            d.nome AS disciplina,
            n.bimestre,
            n.valor AS nota, 
            n.data_lancamento
        FROM Notas n
        JOIN Alunos a ON a.id = n.id_aluno
        JOIN Disciplinas d ON d.id = n.id_disciplina
        ORDER BY n.data_lancamento DESC
        """
    )

    if df_notas.empty:
        st.info("Sem notas registradas ainda. Cadastre na aba **Notas & Atividades**.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            fig_hist = px.histogram(df_notas, x="nota", nbins=10, title="Distribuição de notas (0–10)")
            st.plotly_chart(fig_hist, use_container_width=True)
        with c2:
            fig_box = px.box(df_notas, x="disciplina", y="nota", points="all", title="Notas por disciplina")
            st.plotly_chart(fig_box, use_container_width=True)

    st.subheader("Frequência — presença por turma (últimos 30 dias)")
    
    # <--- CORREÇÃO: Consulta de frequência reescrita
    df_freq = get_df(
        """
        SELECT 
            t.nome AS turma,
            AVG(CASE WHEN f.status='Presente' THEN 1.0 ELSE 0 END) AS indice_presenca
        FROM Frequencia f
        JOIN Alunos a ON a.id = f.id_aluno
        LEFT JOIN Turmas t ON t.id = a.id_turma
        WHERE date(f.data_aula) >= date('now','-30 day')
        GROUP BY t.nome
        ORDER BY indice_presenca DESC
        """
    )
    if df_freq.empty:
        st.info("Sem presenças registradas nos últimos 30 dias. Use a aba **Frequência**.")
    else:
        st.bar_chart(df_freq.set_index("turma"))

# -------------------- Notas & Atividades -------------------- #
with abas[1]:
    st.subheader("Lançar nota")
    # <--- CORREÇÃO: Lógica de lançamento de notas adaptada
    df_alunos = get_df("SELECT id, nome_completo FROM Alunos ORDER BY nome_completo")
    df_disc = get_df("SELECT id, nome FROM Disciplinas ORDER BY nome")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        aluno_sel = st.selectbox("Aluno", options=df_alunos["nome_completo"].tolist(), key="sel_aluno_nota")
    with c2:
        disc_sel = st.selectbox("Disciplina", options=df_disc["nome"].tolist(), key="sel_disc_nota")
    with c3:
        bimestre = st.selectbox("Bimestre", options=[1, 2, 3, 4])
    with c4:
        nota = st.number_input("Nota (0–10)", 0.0, 10.0, step=0.5)

    if st.button("Registrar nota", disabled=df_alunos.empty or df_disc.empty):
        try:
            aluno_id = int(df_alunos[df_alunos.nome_completo == aluno_sel].id.iat[0])
            disc_id = int(df_disc[df_disc.nome == disc_sel].id.iat[0])
            # <--- CORREÇÃO: INSERT adaptado para nova tabela Notas
            execute("INSERT INTO Notas (id_aluno, id_disciplina, bimestre, valor) VALUES (?,?,?,?)", (aluno_id, disc_id, bimestre, float(nota)))
            st.success("Nota registrada!")
            st.cache_data.clear() # Limpa o cache para atualizar os gráficos
        except Exception as e:
            st.error(f"Erro ao registrar nota: {e}")
            
    st.divider()
    st.subheader("Visualizar Atividades e Notas Lançadas")
    # ... (A visualização de notas lançadas pode ser mais complexa e adicionada aqui)
    df_view_notas = get_df("""
        SELECT a.nome_completo as Aluno, d.nome as Disciplina, n.bimestre, n.valor as Nota, n.data_lancamento as Data
        FROM Notas n
        JOIN Alunos a ON a.id = n.id_aluno
        JOIN Disciplinas d ON d.id = n.id_disciplina
        ORDER BY n.data_lancamento DESC
    """)
    st.dataframe(df_view_notas, use_container_width=True)

# -------------------- Frequência -------------------- #
with abas[2]:
    st.subheader("Registro de frequência")
    df_alunos2 = get_df("SELECT id, nome_completo FROM Alunos ORDER BY nome_completo")
    df_disc2 = get_df("SELECT id, nome FROM Disciplinas ORDER BY nome")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        aluno_sel2 = st.selectbox("Aluno", options=df_alunos2["nome_completo"].tolist(), key="sel_aluno_freq")
    with c2:
        # <--- CORREÇÃO: Adicionado seletor de disciplina, pois é obrigatório
        disc_sel2 = st.selectbox("Disciplina", options=df_disc2["nome"].tolist(), key="sel_disc_freq")
    with c3:
        data_freq = st.date_input("Data da aula", value=date.today())
    with c4:
        status = st.radio("Status", ["Presente", "Ausente"], horizontal=True)

    if st.button("Salvar presença", disabled=df_alunos2.empty or df_disc2.empty):
        try:
            aluno_id2 = int(df_alunos2[df_alunos2.nome_completo == aluno_sel2].id.iat[0])
            disc_id2 = int(df_disc2[df_disc2.nome == disc_sel2].id.iat[0])
            # <--- CORREÇÃO: INSERT adaptado para nova tabela Frequencia
            execute(
                "INSERT INTO Frequencia (id_aluno, id_disciplina, data_aula, status) VALUES (?,?,?,?)",
                (aluno_id2, disc_id2, data_freq.isoformat(), status),
            )
            st.success("Presença salva!")
            st.cache_data.clear()
        except Exception as e:
            st.error(f"Erro ao salvar presença: {e}")

# -------------------- Comunicação -------------------- #
with abas[3]:
    st.subheader("Publicar aviso")
    titulo_av = st.text_input("Título do Aviso")
    msg_av = st.text_area("Mensagem do Aviso", height=120)

    if st.button("Enviar aviso", type="primary", disabled=not (titulo_av and msg_av)):
        # <--- CORREÇÃO: Lógica de 'público' removida. 'id_gestor' é hardcoded como 1.
        # Numa versão completa, pegaríamos o ID do gestor logado.
        execute(
            "INSERT INTO Avisos (titulo, mensagem, id_gestor) VALUES (?,?,?)",
            (titulo_av.strip(), msg_av.strip(), 1),
        )
        st.success("Aviso publicado!")
        st.cache_data.clear()

    st.divider()
    st.subheader("Avisos recentes")
    # <--- CORREÇÃO: Consulta de avisos simplificada
    df_av = get_df("SELECT data_envio AS Data, titulo AS Título, mensagem AS Mensagem FROM Avisos ORDER BY data_envio DESC")
    st.dataframe(df_av, use_container_width=True)

# -------------------- Cadastros -------------------- #
with abas[4]:
    st.subheader("Cadastros básicos")
    tab1, tab2, tab3, tab4 = st.tabs(["Alunos", "Turmas", "Disciplinas", "Usuários"])

    with tab1: # Alunos
        df_turmas_cad = get_df("SELECT id, nome FROM Turmas ORDER BY nome")
        df_resp_cad = get_df("SELECT id, nome FROM Usuarios WHERE perfil='responsavel' ORDER BY nome")

        nome_aluno = st.text_input("Nome completo do aluno")
        nasc_aluno = st.date_input("Data de nascimento", min_value=date(1990, 1, 1), value=date(2010, 1, 1))
        turma_aluno = st.selectbox("Turma", options=df_turmas_cad.nome.tolist())
        resp_aluno = st.selectbox("Responsável", options=df_resp_cad.nome.tolist())

        if st.button("Adicionar aluno", disabled=not nome_aluno):
            turma_id = int(df_turmas_cad[df_turmas_cad.nome == turma_aluno].id.iat[0])
            resp_id = int(df_resp_cad[df_resp_cad.nome == resp_aluno].id.iat[0])
            execute(
                "INSERT INTO Alunos (nome_completo, data_nascimento, id_turma, id_responsavel) VALUES (?,?,?,?)",
                (nome_aluno.strip(), nasc_aluno.isoformat(), turma_id, resp_id),
            )
            st.success("Aluno cadastrado!")
            st.cache_data.clear()

    with tab2: # Turmas
        c1, c2 = st.columns(2)
        nome_turma = c1.text_input("Nome da turma (ex.: 1ºA)")
        ano_letivo = c2.number_input("Ano letivo", min_value=2020, max_value=2030, value=date.today().year)

        if st.button("Adicionar turma", disabled=not nome_turma):
            execute("INSERT INTO Turmas (nome, ano_letivo) VALUES (?,?)", (nome_turma.strip(), ano_letivo))
            st.success("Turma adicionada!")
            st.cache_data.clear()

    with tab3: # Disciplinas
        nome_disc = st.text_input("Nome da disciplina")
        if st.button("Adicionar disciplina", disabled=not nome_disc):
            execute("INSERT INTO Disciplinas (nome) VALUES (?)", (nome_disc.strip(),))
            st.success("Disciplina adicionada!")
            st.cache_data.clear()
    
    with tab4: # Usuários
        nome_user = st.text_input("Nome do usuário")
        email_user = st.text_input("Email do usuário")
        senha_user = st.text_input("Senha", type="password")
        perfil_user = st.selectbox("Perfil", options=['gestor', 'professor', 'responsavel'])

        if st.button("Adicionar usuário", disabled=not(nome_user and email_user and senha_user)):
            # NOTA: Em um app real, a senha seria criptografada (hash)
            execute("INSERT INTO Usuarios (nome, email, senha_hash, perfil) VALUES (?, ?, ?, ?)",
                    (nome_user, email_user, senha_user, perfil_user))
            st.success("Usuário cadastrado!")
            st.cache_data.clear()
