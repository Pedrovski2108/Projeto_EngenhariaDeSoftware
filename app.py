# app.py — MVP Sistema de Gestão Escolar
# Autor: Pedro / assistência
# Como executar:  
# 1) pip install streamlit pandas plotly
# 2) streamlit run app.py
import os
import sqlite3
from contextlib import closing
from datetime import date, datetime

import pandas as pd
import plotly.express as px
import streamlit as st

DB_PATH = "escola.db"

# -------------------- Utilidades de Banco -------------------- #

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    db_path = os.path.join(os.path.dirname(__file__), "escola.db")
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")

    with sqlite3.connect(db_path) as conn:
        with open(schema_path, encoding="utf-8") as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)
    print("Banco de dados inicializado com sucesso!")

@st.cache_data(show_spinner=False)
def get_df(sql: str, params: tuple | list = ()):  # leitura com cache
    with closing(get_conn()) as conn:
        return pd.read_sql(sql, conn, params=params)


def execute(sql: str, params: tuple | list = ()):  # escrita sem cache
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        return cur.lastrowid


# -------------------- UI Base -------------------- #

st.set_page_config(page_title="Gestão Escolar — MVP", layout="wide")
st.title("📚 Sistema de Gestão Escolar — MVP")

# Tenta criar tabelas mínimas se ainda não existirem
init_db()

with st.sidebar:
    st.header("🔐 Perfil de acesso (simples)")
    perfil = st.radio(
        "Escolha seu perfil",
        options=["Gestor", "Professor", "Responsável"],
        index=1,
    )
    st.divider()
    st.caption("Banco de dados: ")
    st.code(DB_PATH)

abas = st.tabs([
    "🏠 Dashboard",
    "📝 Notas & Atividades",
    "✅ Frequência",
    "📣 Comunicação",
    "⚙️ Cadastros básicos",
])

# -------------------- Dashboard -------------------- #
with abas[0]:
    colA, colB, colC, colD = st.columns(4)
    total_alunos = get_df("SELECT COUNT(*) c FROM alunos")["c"].iat[0]
    total_turmas = get_df("SELECT COUNT(*) c FROM turmas")["c"].iat[0]
    total_disciplinas = get_df("SELECT COUNT(*) c FROM disciplinas")["c"].iat[0]
    total_avisos = get_df("SELECT COUNT(*) c FROM avisos")["c"].iat[0]

    colA.metric("Alunos", total_alunos)
    colB.metric("Turmas", total_turmas)
    colC.metric("Disciplinas", total_disciplinas)
    colD.metric("Avisos", total_avisos)

    st.subheader("Rendimento — distribuição de notas")
    df_notas = get_df(
        """
        SELECT n.id, a.nome AS aluno, d.nome AS disciplina, atv.titulo AS atividade, n.nota, n.data_registro
        FROM notas n
        JOIN alunos a ON a.id=n.aluno_id
        JOIN atividades atv ON atv.id=n.atividade_id
        JOIN disciplinas d ON d.id=atv.disciplina_id
        ORDER BY n.data_registro DESC
        """
    )

    if df_notas.empty:
        st.info("Sem notas registradas ainda. Cadastre na aba **Notas & Atividades**.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            fig_hist = px.histogram(df_notas, x="nota", nbins=20, title="Distribuição de notas (0–10)")
            st.plotly_chart(fig_hist, use_container_width=True)
        with c2:
            fig_box = px.box(
                df_notas,
                x="disciplina",
                y="nota",
                points="all",
                title="Notas por disciplina",
            )
            st.plotly_chart(fig_box, use_container_width=True)

    st.subheader("Frequência — presença por turma (últimos 30 dias)")
    df_freq = get_df(
        """
        SELECT t.nome turma,
               AVG(CASE WHEN f.status='Presente' THEN 1.0 WHEN f.status='Justificado' THEN 0.8 ELSE 0 END) AS indice_presenca
        FROM frequencias f
        JOIN alunos a ON a.id=f.aluno_id
        LEFT JOIN turmas t ON t.id=a.turma_id
        WHERE date(f.data) >= date('now','-30 day')
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
    st.subheader("Cadastrar atividade")
    df_disc = get_df("SELECT id, nome FROM disciplinas ORDER BY nome")
    if df_disc.empty:
        st.warning("Cadastre ao menos uma **Disciplina** em *Cadastros básicos*.")
    col1, col2 = st.columns(2)
    with col1:
        disc_escolhida = st.selectbox("Disciplina", options=df_disc["nome"].tolist()) if not df_disc.empty else None
        titulo = st.text_input("Título da atividade")
    with col2:
        data_atividade = st.date_input("Data", value=date.today())
        descricao = st.text_area("Descrição (opcional)", height=80)

    if st.button("Salvar atividade", type="primary", disabled=df_disc.empty or not titulo):
        if df_disc.empty:
            st.error("Cadastre uma disciplina primeiro.")
        else:
            disc_id = int(df_disc[df_disc.nome == disc_escolhida].id.iat[0])
            execute(
                "INSERT INTO atividades (disciplina_id, titulo, descricao, data) VALUES (?,?,?,?)",
                (disc_id, titulo.strip(), descricao.strip(), data_atividade.isoformat()),
            )
            st.success("Atividade cadastrada!")
            st.cache_data.clear()

    st.divider()
    st.subheader("Lançar nota")
    df_alunos = get_df("SELECT id, nome FROM alunos ORDER BY nome")
    df_atv = get_df(
        "SELECT a.id, a.titulo || ' — ' || d.nome || ' (' || a.data || ')' AS rotulo FROM atividades a JOIN disciplinas d ON d.id=a.disciplina_id ORDER BY a.data DESC"
    )
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        aluno_sel = st.selectbox("Aluno", options=df_alunos["nome"].tolist() if not df_alunos.empty else [])
    with c2:
        atv_sel = st.selectbox("Atividade", options=df_atv["rotulo"].tolist() if not df_atv.empty else [])
    with c3:
        nota = st.number_input("Nota (0–10)", 0.0, 10.0, step=0.5)

    if st.button("Registrar nota", disabled=df_alunos.empty or df_atv.empty):
        try:
            aluno_id = int(df_alunos[df_alunos.nome == aluno_sel].id.iat[0])
            atv_id = int(df_atv[df_atv.rotulo == atv_sel].id.iat[0])
            execute("INSERT OR REPLACE INTO notas (aluno_id, atividade_id, nota) VALUES (?,?,?)", (aluno_id, atv_id, float(nota)))
            
            st.success("Nota registrada!")
            st.cache_data.clear()
        except Exception as e:
            st.error(f"Erro ao registrar nota: {e}")

    st.divider()
    st.subheader("Notas lançadas")
    st.caption("Filtre por turma, disciplina ou aluno")

    colf1, colf2, colf3 = st.columns(3)
    turmas = get_df("SELECT id, nome FROM turmas ORDER BY nome")
    turma_f = colf1.selectbox("Turma", ["Todas"] + turmas.nome.tolist())
    disc_f = colf2.selectbox("Disciplina", ["Todas"] + df_disc.nome.tolist())
    aluno_f = colf3.text_input("Aluno (contém)")

    base_sql = (
        "SELECT n.id, a.nome AS Aluno, t.nome AS Turma, d.nome AS Disciplina, atv.titulo AS Atividade, n.nota AS Nota, atv.data AS Data "
        "FROM notas n JOIN alunos a ON a.id=n.aluno_id "
        "LEFT JOIN turmas t ON t.id=a.turma_id "
        "JOIN atividades atv ON atv.id=n.atividade_id "
        "JOIN disciplinas d ON d.id=atv.disciplina_id WHERE 1=1"
    )

    params = []
    if turma_f != "Todas":
        base_sql += " AND t.nome=?"
        params.append(turma_f)
    if disc_f != "Todas":
        base_sql += " AND d.nome=?"
        params.append(disc_f)
    if aluno_f.strip():
        base_sql += " AND a.nome LIKE ?"
        params.append(f"%{aluno_f.strip()}%")

    base_sql += " ORDER BY atv.data DESC, a.nome"
    df_view = get_df(base_sql, params)
    st.dataframe(df_view, use_container_width=True)

# -------------------- Frequência -------------------- #
with abas[2]:
    st.subheader("Registro de frequência (por aluno)")
    df_alunos2 = get_df("SELECT id, nome FROM alunos ORDER BY nome")
    c1, c2, c3 = st.columns(3)
    with c1:
        aluno_sel2 = st.selectbox("Aluno", options=df_alunos2.nome.tolist() if not df_alunos2.empty else [])
    with c2:
        data_freq = st.date_input("Data", value=date.today())
    with c3:
        status = st.radio("Status", ["Presente", "Ausente", "Justificado"], horizontal=True)

    if st.button("Salvar presença", disabled=df_alunos2.empty):
        try:
            aluno_id2 = int(df_alunos2[df_alunos2.nome == aluno_sel2].id.iat[0])
            execute(
                "INSERT OR REPLACE INTO frequencias (aluno_id, data, status) VALUES (?,?,?)",
                (aluno_id2, data_freq.isoformat(), status),
            )
            st.success("Presença salva!")
            st.cache_data.clear()
        except Exception as e:
            st.error(f"Erro: {e}")

    st.divider()
    st.subheader("Resumo da turma (últimos 15 dias)")
    turmas2 = get_df("SELECT id, nome FROM turmas ORDER BY nome")
    turma_escolhida = st.selectbox("Turma", options=turmas2.nome.tolist() if not turmas2.empty else [])

    if turma_escolhida:
        df_turma = get_df(
            """
            SELECT a.nome AS Aluno, f.data AS Data, f.status AS Status
            FROM alunos a
            JOIN frequencias f ON f.aluno_id=a.id
            JOIN turmas t ON t.id=a.turma_id
            WHERE t.nome=? AND date(f.data) >= date('now','-15 day')
            ORDER BY f.data DESC, a.nome
            """,
            (turma_escolhida,),
        )
        if df_turma.empty:
            st.info("Sem registros para o período.")
        else:
            st.dataframe(df_turma, use_container_width=True)

# -------------------- Comunicação -------------------- #
with abas[3]:
    st.subheader("Publicar aviso")
    c1, c2 = st.columns([2, 1])
    with c1:
        titulo_av = st.text_input("Título")
        msg_av = st.text_area("Mensagem", height=120)
    with c2:
        publico = st.selectbox("Público", ["Todos", "Responsáveis", "Professores", "Gestores"])
        st.caption("Data de criação automática")

    if st.button("Enviar aviso", type="primary", disabled=not (titulo_av and msg_av)):
        execute(
            "INSERT INTO avisos (titulo, mensagem, publico) VALUES (?,?,?)",
            (titulo_av.strip(), msg_av.strip(), publico),
        )
        st.success("Aviso publicado!")
        st.cache_data.clear()

    st.divider()
    st.subheader("Avisos recentes")
    filtro_pub = st.multiselect("Filtrar por público", ["Todos", "Responsáveis", "Professores", "Gestores"], default=["Todos"])
    sql_avisos = "SELECT data_criacao AS Data, publico AS Público, titulo AS Título, mensagem AS Mensagem FROM avisos WHERE 1=1"
    params = []
    if filtro_pub:
        sql_avisos += " AND publico IN (" + ",".join(["?"] * len(filtro_pub)) + ")"
        params.extend(filtro_pub)
    sql_avisos += " ORDER BY data_criacao DESC LIMIT 100"
    df_av = get_df(sql_avisos, params)
    st.dataframe(df_av, use_container_width=True)

# -------------------- Cadastros -------------------- #
with abas[4]:
    st.subheader("Cadastros básicos (mínimo viável)")
    tab1, tab2, tab3 = st.tabs(["Alunos", "Turmas", "Disciplinas"])

    with tab1:
        colA, colB = st.columns([2, 1])
        with colA:
            nome_aluno = st.text_input("Nome do aluno")
            lista_turmas = get_df("SELECT id, nome FROM turmas ORDER BY nome")
            turma_aluno = st.selectbox("Turma", options=lista_turmas.nome.tolist() if not lista_turmas.empty else [])
            responsavel = st.text_input("Responsável (nome)")
        with colB:
            st.caption("Campos obrigatórios: Nome")
        if st.button("Adicionar aluno", disabled=not nome_aluno):
            turma_id = (
                int(lista_turmas[lista_turmas.nome == turma_aluno].id.iat[0]) if not lista_turmas.empty and turma_aluno else None
            )
            execute(
                "INSERT INTO alunos (nome, turma_id, responsavel) VALUES (?,?,?)",
                (nome_aluno.strip(), turma_id, responsavel.strip() if responsavel else None),
            )
            st.success("Aluno cadastrado!")
            st.cache_data.clear()

        st.markdown("**Alunos cadastrados**")
        df_al = get_df(
            "SELECT a.id, a.nome, t.nome AS turma, a.responsavel FROM alunos a LEFT JOIN turmas t ON t.id=a.turma_id ORDER BY a.nome"
        )
        st.dataframe(df_al, use_container_width=True)

    with tab2:
        nome_turma = st.text_input("Nome da turma (ex.: 1ºA)")
        if st.button("Adicionar turma", disabled=not nome_turma):
            try:
                execute("INSERT INTO turmas (nome) VALUES (?)", (nome_turma.strip(),))
                st.success("Turma adicionada!")
                st.cache_data.clear()
            except sqlite3.IntegrityError:
                st.error("Turma já existe.")
        st.markdown("**Turmas**")
        st.dataframe(get_df("SELECT * FROM turmas ORDER BY nome"), use_container_width=True)

    with tab3:
        nome_disc = st.text_input("Nome da disciplina")
        if st.button("Adicionar disciplina", disabled=not nome_disc):
            try:
                execute("INSERT INTO disciplinas (nome) VALUES (?)", (nome_disc.strip(),))
                st.success("Disciplina adicionada!")
                st.cache_data.clear()
            except sqlite3.IntegrityError:
                st.error("Disciplina já existe.")
        st.markdown("**Disciplinas**")
        st.dataframe(get_df("SELECT * FROM disciplinas ORDER BY nome"), use_container_width=True)

# -------------------- Rodapé -------------------- #
st.caption(
    "MVP com foco em: cadastro básico, lançamento de notas, registro de frequência, comunicação e dashboard simples."
)
