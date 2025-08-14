-- Habilita o uso de chaves estrangeiras no SQLite para garantir a integridade dos dados.
PRAGMA foreign_keys = ON;

-- -----------------------------------------------------
-- Tabela `Usuarios`
-- Armazena todos os usuários que podem fazer login: gestores, professores e responsáveis.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS Usuarios (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nome TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  senha_hash TEXT NOT NULL,
  perfil TEXT NOT NULL CHECK(perfil IN ('gestor', 'professor', 'responsavel'))
);

-- -----------------------------------------------------
-- Tabela `Turmas`
-- Define as turmas da escola. Ex: "8º Ano A", "9º Ano B".
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS Turmas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nome TEXT NOT NULL,
  ano_letivo INTEGER NOT NULL
);

-- -----------------------------------------------------
-- Tabela `Alunos`
-- Armazena os dados dos alunos e os vincula a uma turma e a um responsável.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS Alunos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nome_completo TEXT NOT NULL,
  data_nascimento DATE NOT NULL,
  id_turma INTEGER,
  id_responsavel INTEGER,
  FOREIGN KEY (id_turma) REFERENCES Turmas (id),
  FOREIGN KEY (id_responsavel) REFERENCES Usuarios (id)
);

-- -----------------------------------------------------
-- Tabela `Disciplinas`
-- Catálogo de todas as disciplinas oferecidas pela escola.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS Disciplinas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nome TEXT NOT NULL UNIQUE
);

-- -----------------------------------------------------
-- Tabela `Professor_Turma_Disciplina`
-- Tabela de ligação que define qual professor leciona qual disciplina para qual turma.
-- Esta é uma tabela crucial para a lógica do sistema.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS Professor_Turma_Disciplina (
  id_professor INTEGER NOT NULL,
  id_turma INTEGER NOT NULL,
  id_disciplina INTEGER NOT NULL,
  PRIMARY KEY (id_professor, id_turma, id_disciplina),
  FOREIGN KEY (id_professor) REFERENCES Usuarios (id),
  FOREIGN KEY (id_turma) REFERENCES Turmas (id),
  FOREIGN KEY (id_disciplina) REFERENCES Disciplinas (id)
);

-- -----------------------------------------------------
-- Tabela `Notas`
-- Armazena as notas dos alunos por disciplina e bimestre/período.
-- -----------------------------------------------------
CREATE TABLE Notas (
    id_nota INTEGER PRIMARY KEY AUTOINCREMENT,
    valor REAL NOT NULL,
    bimestre INTEGER NOT NULL CHECK(bimestre IN (1, 2, 3, 4)),
    id_aluno INTEGER NOT NULL,
    id_disciplina INTEGER NOT NULL,
    data_lancamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_aluno) REFERENCES Alunos (id_aluno) ON DELETE CASCADE,
    FOREIGN KEY (id_disciplina) REFERENCES Disciplinas (id_disciplina) ON DELETE CASCADE
);

-- -----------------------------------------------------
-- Tabela `Frequencia`
-- Registra a presença ou ausência dos alunos em uma data de aula específica.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS Frequencia (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  data_aula DATE NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('Presente', 'Ausente')),
  id_aluno INTEGER NOT NULL,
  id_disciplina INTEGER NOT NULL,
  FOREIGN KEY (id_aluno) REFERENCES Alunos (id),
  FOREIGN KEY (id_disciplina) REFERENCES Disciplinas (id)
);

-- -----------------------------------------------------
-- Tabela `Avisos`
-- Para comunicação geral da gestão da escola com os responsáveis.
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS Avisos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  titulo TEXT NOT NULL,
  mensagem TEXT NOT NULL,
  data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  id_gestor INTEGER NOT NULL,
  FOREIGN KEY (id_gestor) REFERENCES Usuarios (id)
);

CREATE TABLE IF NOT EXISTS atividades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_disciplina INTEGER NOT NULL,
    titulo TEXT NOT NULL,
    descricao TEXT,
    data DATE NOT NULL,
    FOREIGN KEY (id_disciplina) REFERENCES Disciplinas(id)
);