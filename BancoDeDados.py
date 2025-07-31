import sqlite3

CREATE TABLE IF NOT EXISTS Usuarios (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nome TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  senha_hash TEXT NOT NULL,
  perfil TEXT NOT NULL CHECK(perfil IN ('gestor', 'professor', 'responsavel'))
);


CREATE TABLE IF NOT EXISTS Turmas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nome TEXT NOT NULL, -- Ex: "9º Ano B"
  ano_letivo INTEGER NOT NULL -- Ex: 2024
);

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
-- Catálogo de todas as disciplinas oferecidas
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS Disciplinas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nome TEXT NOT NULL UNIQUE -- Ex: "Matemática"
);

-- -----------------------------------------------------
-- Tabela `Professor_Turma_Disciplina`
-- Tabela de ligação que associa um professor a uma disciplina em uma turma específica
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
-- Armazena as notas dos alunos por disciplina e bimestre
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS Notas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  valor REAL NOT NULL,
  bimestre INTEGER NOT NULL CHECK(bimestre IN (1, 2, 3, 4)),
  id_aluno INTEGER NOT NULL,
  id_disciplina INTEGER NOT NULL,
  data_lancamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (id_aluno) REFERENCES Alunos (id),
  FOREIGN KEY (id_disciplina) REFERENCES Disciplinas (id)
);

-- -----------------------------------------------------
-- Tabela `Frequencia`
-- Registra a presença ou ausência dos alunos
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
-- Para comunicação geral da escola
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS Avisos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  titulo TEXT NOT NULL,
  mensagem TEXT NOT NULL,
  data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  id_gestor INTEGER NOT NULL, -- Quem enviou o aviso
  FOREIGN KEY (id_gestor) REFERENCES Usuarios (id)
);
