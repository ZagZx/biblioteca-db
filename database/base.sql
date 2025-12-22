CREATE DATABASE db_trabalho3b;
USE db_trabalho3b;

CREATE TABLE autores (
    id_autor INT AUTO_INCREMENT PRIMARY KEY,
    nome_autor VARCHAR(255) NOT NULL,
    nacionalidade VARCHAR(255),
    data_nascimento DATE,
    biografia TEXT
);

CREATE TABLE generos (
    id_genero INT AUTO_INCREMENT PRIMARY KEY,
    nome_genero VARCHAR(255) NOT NULL
);

CREATE TABLE editoras (
    id_editora INT AUTO_INCREMENT PRIMARY KEY,
    nome_editora VARCHAR(255) NOT NULL,
    endereco_editora TEXT
);

CREATE TABLE livros (
    id_livro INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    autor_id INT NOT NULL,
    isbn VARCHAR(13) UNIQUE NOT NULL,
    ano_publicacao INT,
    genero_id INT NOT NULL,
    editora_id INT NOT NULL,
    quantidade_disponivel INT NOT NULL,
    resumo TEXT,
    FOREIGN KEY (autor_id) REFERENCES autores(id_autor),
    FOREIGN KEY (genero_id) REFERENCES generos(id_genero),
    FOREIGN KEY (editora_id) ReFERENCES editoras(id_editora)
);

CREATE TABLE usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nome_usuario VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,
    numero_telefone VARCHAR(15),
    data_inscricao DATE NOT NULL,
    multa_atual DECIMAL(10, 2) NOT NULL DEFAULT(0),
    admin BOOLEAN NOT NULL DEFAULT 0 
);

CREATE TABLE emprestimos (
    id_emprestimo INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    livro_id INT NOT NULL,
    data_emprestimo DATE NOT NULL,
    data_devolucao_prevista DATE NOT NULL,
    data_devolucao_real DATE,
    status_emprestimo ENUM('pendente', 'devolvido', 'atrasado') NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (livro_id) REFERENCES livros(id_livro) ON DELETE CASCADE
);

CREATE TABLE logs(
	id INT AUTO_INCREMENT PRIMARY KEY,
    tabela ENUM('autores', 'editoras', 'emprestimos', 'generos', 'livros', 'usuarios') NOT NULL,
    acao ENUM('update', 'delete') NOT NULL,
    data_alteracao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    registro_id INT NOT NULL,
    dados_antigos JSON NOT NULL,
    dados_atuais JSON
    -- usuario_id INT NOT NULL, 
    -- FOREIGN KEY (usuario_id) REFERENCES usuarios(id_usuario)
);
