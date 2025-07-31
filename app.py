import streamlit as st
import sqlite3
import pandas as pd
import os
#APP TESTE 
# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
DB_FILE = "escola.db"

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def setup_database():
    """
    Função completa para criar e popular o banco de dados do zero.
    Garante a ordem correta de inserção para evitar erros de Foreign Key.
    """
    # Deleta o banco antigo, se existir, para garantir um começo limpo
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    print("Criando e populando o banco de dados...")
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Cria a estrutura das tabelas a partir do arquivo schema.sql
    with open('schema.sql', 'r', encoding='utf-8') as f:
        cursor.executescript(f.read())

    # 2. Insere os dados de exemplo NA ORDEM CORRETA
    try:
        # Inserindo dados que não dependem de outros (Tabelas "Pai")
        cursor.execute("INSERT INTO Disciplinas (id, nome) VALUES (1, 'Matemática'), (2, 'Português'), (3, 'Ciências');")
        cursor.execute("INSERT INTO Turmas (id, nome, ano_letivo) VALUES (1, '8º Ano A', 2025), (2, '9º Ano B', 2025);")
        cursor.execute("""
            INSERT INTO Usuarios (id, nome, email, senha_hash, perfil) VALUES
            (1, 'Ana Silva (Gestora)', 'ana.gestora@escola.com', 'hash1', 'gestor'),
            (2, 'Prof. Carlos Alberto', 'carlos.prof@escola.com', 'hash2', 'professor'),
            (3, 'Sr. João Pereira', 'joao.pai@email.com', 'hash3', 'responsavel'),
            (4, 'Sra. Maria Souza', 'maria.mae@email.com', 'hash4', 'responsavel'),
            (5, 'Prof. Beatriz Lima', 'beatriz.prof@escola.com', 'hash5', 'professor');
        """)

        # Agora, inserindo dados que dependem dos registros acima (Tabelas "Filho")
        # ESTE É O INSERT QUE ESTAVA CAUSANDO O ERRO. AGORA ELE VAI FUNCIONAR.
        cursor.execute("""
            INSERT INTO Alunos (id, nome_completo, data_nascimento, id_turma, id_responsavel) VALUES
            (1, 'Lucas Pereira da Silva', '2011-05-10', 1, 3), -- Turma 1 e Responsável 3 existem
            (2, 'Mariana Souza Costa', '2011-08-22', 1, 4);   -- Turma 1 e Responsável 4 existem
        """)
        
        # Inserindo as associações de professores
        cursor.execute("""
            INSERT INTO Professor_Turma_Disciplina (id_professor, id_turma, id_disciplina) VALUES
            (2, 1, 1), -- Prof. Carlos (ID 2) -> Turma 8º Ano A (ID 1) -> Matemática (ID 1)
            (5, 1, 3); -- Prof. Beatriz (ID 5) -> Turma 8º Ano A (ID 1) -> Ciências (ID 3)
        """)

        # Inserindo uma nota de exemplo
        cursor.execute("INSERT INTO Notas (valor, bimestre, id_aluno, id_disciplina) VALUES (8.5, 1, 1, 1);")

        conn.commit()
        print("Banco de dados criado e populado com sucesso!")

    except sqlite3.Error as e:
        print(f"Ocorreu um erro ao inserir os dados: {e}")
        conn.rollback() # Desfaz as alterações em caso de erro
    finally:
        conn.close()
# --- FUNÇÕES DE CONSULTA AO BANCO ---

def get_professor_turmas(id_professor):
    """Busca as turmas que um professor leciona."""
    conn = get_db_connection()
    query = """
        SELECT DISTINCT T.id, T.nome
        FROM Turmas T
        JOIN Professor_Turma_Disciplina PTD ON T.id = PTD.id_turma
        WHERE PTD.id_professor = ?
    """
    turmas = pd.read_sql_query(query, conn, params=(id_professor,))
    conn.close()
    return turmas

def get_professor_disciplinas(id_professor, id_turma):
    """Busca as disciplinas que um professor leciona em uma turma específica."""
    conn = get_db_connection()
    query = """
        SELECT DISTINCT D.id, D.nome
        FROM Disciplinas D
        JOIN Professor_Turma_Disciplina PTD ON D.id = PTD.id_disciplina
        WHERE PTD.id_professor = ? AND PTD.id_turma = ?
    """
    disciplinas = pd.read_sql_query(query, conn, params=(id_professor, id_turma))
    conn.close()
    return disciplinas

def get_alunos_e_notas(id_turma, id_disciplina, bimestre):
    """Busca alunos de uma turma e suas notas na disciplina e bimestre selecionados."""
    conn = get_db_connection()
    query = """
        SELECT
            A.id AS id_aluno,
            A.nome_completo,
            N.valor AS nota
        FROM Alunos A
        LEFT JOIN Notas N ON A.id = N.id_aluno
                          AND N.id_disciplina = ?
                          AND N.bimestre = ?
        WHERE A.id_turma = ?
    """
    df = pd.read_sql_query(query, conn, params=(id_disciplina, bimestre, id_turma))
    conn.close()
    return df

def salvar_notas(df_notas):
    """Atualiza ou insere as notas no banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    for index, row in df_notas.iterrows():
        # Verifica se a nota não é nula (o usuário pode ter apagado)
        if pd.notna(row['nota']):
            # Tenta atualizar uma nota existente
            cursor.execute("""
                UPDATE Notas SET valor = ?
                WHERE id_aluno = ? AND id_disciplina = ? AND bimestre = ?
            """, (row['nota'], row['id_aluno'], row['id_disciplina'], row['bimestre']))

            # Se nenhuma linha foi atualizada, insere uma nova nota
            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO Notas (id_aluno, id_disciplina, bimestre, valor)
                    VALUES (?, ?, ?, ?)
                """, (row['id_aluno'], row['id_disciplina'], row['bimestre'], row['nota']))
        else:
            # Se a nota for nula/vazia, remove o registro do banco
            cursor.execute("""
                DELETE FROM Notas
                WHERE id_aluno = ? AND id_disciplina = ? AND bimestre = ?
            """, (row['id_aluno'], row['id_disciplina'], row['bimestre']))

    conn.commit()
    conn.close()

# --- INTERFACE DA APLICAÇÃO STREAMLIT ---

# Inicializa o banco de dados na primeira execução
setup_database()

st.set_page_config(layout="wide")
st.title(" Lançamento de Notas")
st.markdown("### Área do Professor")

# Simulação de Login: Em um sistema real, isso viria de um sistema de autenticação
# ID 2 = Prof. Carlos
ID_PROFESSOR_LOGADO = 2
st.info(f"Professor logado: **Prof. Carlos** (ID: {ID_PROFESSOR_LOGADO})")

# 1. Seleção de Turma
turmas = get_professor_turmas(ID_PROFESSOR_LOGADO)
if turmas.empty:
    st.warning("Você não está associado a nenhuma turma.")
else:
    # Usamos o nome da turma para exibição e o id como valor
    turma_selecionada_nome = st.selectbox("Selecione a Turma", options=turmas['nome'])
    id_turma_selecionada = turmas.loc[turmas['nome'] == turma_selecionada_nome, 'id'].iloc[0]

    # 2. Seleção de Disciplina (dependente da turma)
    disciplinas = get_professor_disciplinas(ID_PROFESSOR_LOGADO, id_turma_selecionada)
    if disciplinas.empty:
        st.warning("Nenhuma disciplina encontrada para esta turma.")
    else:
        disciplina_selecionada_nome = st.selectbox("Selecione a Disciplina", options=disciplinas['nome'])
        id_disciplina_selecionada = disciplinas.loc[disciplinas['nome'] == disciplina_selecionada_nome, 'id'].iloc[0]

        # 3. Seleção do Bimestre
        bimestre_selecionado = st.selectbox("Selecione o Bimestre", options=[1, 2, 3, 4])

        st.divider()

        # 4. Tabela de Alunos e Notas
        st.markdown(f"#### Lançando notas para **{disciplina_selecionada_nome}** - Turma **{turma_selecionada_nome}** - **{bimestre_selecionado}º Bimestre**")
        
        # Busca os dados atuais
        df_alunos_notas = get_alunos_e_notas(id_turma_selecionada, id_disciplina_selecionada, bimestre_selecionado)

        # Usamos o st.data_editor para criar uma tabela editável
        edited_df = st.data_editor(
            df_alunos_notas,
            column_config={
                "id_aluno": None, # Oculta a coluna de ID do aluno
                "nome_completo": st.column_config.TextColumn("Aluno", disabled=True), # Coluna de texto não editável
                "nota": st.column_config.NumberColumn(
                    "Nota (de 0 a 10)",
                    min_value=0.0,
                    max_value=10.0,
                    step=0.5,
                    format="%.1f",
                )
            },
            hide_index=True,
            num_rows="dynamic" # Permite adicionar/remover linhas (não usaremos para salvar)
        )

        # 5. Botão para Salvar
        if st.button("Salvar Notas", type="primary"):
            # Adiciona colunas auxiliares necessárias para a função de salvar
            edited_df['id_disciplina'] = id_disciplina_selecionada
            edited_df['bimestre'] = bimestre_selecionado
            
            try:
                salvar_notas(edited_df)
                st.success("Notas salvas com sucesso!")
                # Opcional: Recarregar a página ou os dados para confirmar a alteração
                st.rerun()
            except Exception as e:
                st.error(f"Ocorreu um erro ao salvar as notas: {e}")