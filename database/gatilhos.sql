DELIMITER //
-- Pós evento
CREATE TRIGGER 
trg_repoe_livro AFTER UPDATE 
ON emprestimos 
FOR EACH ROW 
BEGIN 
	IF NEW.status_emprestimo = "devolvido" THEN
		UPDATE livros SET quantidade_disponivel = quantidade_disponivel + 1 WHERE id_livro = OLD.livro_id;
	END IF;
END // 

CREATE TRIGGER 
trg_tira_livro AFTER INSERT
ON emprestimos
FOR EACH ROW
BEGIN
	UPDATE livros SET quantidade_disponivel = quantidade_disponivel - 1 WHERE id_livro = NEW.livro_id;
END //

CREATE TRIGGER
trg_repoe_livro_delete AFTER DELETE
ON emprestimos
FOR EACH ROW
BEGIN
    IF OLD.status_emprestimo != "devolvido" THEN
        UPDATE livros SET quantidade_disponivel = quantidade_disponivel + 1 WHERE id_livro = OLD.livro_id;
    END IF ;
END //

CREATE TRIGGER
trg_repoe_livro_delete AFTER DELETE
ON emprestimos
FOR EACH ROW
BEGIN
    IF OLD.status_emprestimo != "devolvido" THEN
        UPDATE livros SET quantidade_disponivel = quantidade_disponivel + 1 WHERE id_livro = OLD.livro_id;
    END IF;
END //

CREATE TRIGGER
trg_multar AFTER UPDATE
ON emprestimos
FOR EACH ROW
BEGIN
	DECLARE dias INTEGER;
	IF OLD.status_emprestimo != "devolvido" THEN
		IF NEW.status_emprestimo = "devolvido" THEN
			IF CURRENT_DATE() > OLD.data_devolucao_prevista THEN
				SET dias = CURRENT_DATE() - OLD.data_devolucao_prevista;
                UPDATE usuarios SET multa_atual = multa_atual + (dias * 0.50) WHERE id_usuario = OLD.usuario_id;
            END IF;
		END IF;
	END IF;
END //

CREATE TRIGGER
trg_descontar_multa AFTER UPDATE
ON emprestimos
FOR EACH ROW
BEGIN
	DECLARE dias INTEGER;
	IF OLD.status_emprestimo != "devolvido" THEN
		IF NEW.status_emprestimo = "devolvido" THEN
			IF CURRENT_DATE() < OLD.data_devolucao_prevista THEN
				SET dias = OLD.data_devolucao_prevista - CURRENT_DATE();
                UPDATE usuarios SET multa_atual = multa_atual - (dias * 0.05) WHERE id_usuario = OLD.usuario_id;
            END IF;
		END IF;
	END IF;
END //

-- triggers validação
-- Impedir quantidade negativa de livros

create trigger trg_corrige_quantidade_livro
before insert on livros
for each row
begin
    if NEW.quantidade_disponivel < 0 then
        set NEW.quantidade_disponivel = 0;
    end if;
end//

-- Ajustar ISBN com tamanho diferente de 13 (se não tiver 13 caracteres , ele vira 0)

create trigger trg_corrige_isbn
before insert on livros
for each row
begin
    if length(NEW.isbn) < 13 then 
        set NEW.isbn = '0000000000000';
    end if;
end//

-- Ajustar data futura (se estiver no futuro coloque na data atual)

create trigger trg_corrige_ano_publicacao_livro
before insert on livros
for each row
begin
    if NEW.ano_publicacao > year(curdate()) then
        set NEW.ano_publicacao = year(curdate());
    end if;
    
end//

-- Impedir títulos de livros vazios

create trigger trg_livros_titulo_validacao
before insert on livros
for each row
begin
    set NEW.titulo = trim(NEW.titulo);

    if NEW.titulo = '' then
        set NEW.titulo = 'TÍTULO NÃO INFORMADO';
    end if;
end;
//


-- Impedir multa negativa do usuário

create trigger trg_usuarios_multa_validacao
before insert on usuarios
for each row
begin
    if NEW.multa_atual < 0 then
        set NEW.multa_atual = 0;
    end if;
end;
//

-- TRIGGERS AUDITORIA

CREATE TRIGGER trg_log_update_livro AFTER UPDATE ON livros
FOR EACH ROW
BEGIN
    INSERT INTO logs(
        tabela,
        acao,
        registro_id,
        dados_antigos,
        dados_atuais
    ) VALUES (
        'livros',
        'update',
        NEW.id_livro,
        JSON_OBJECT( -- DADOS ANTIGOS
			'id_livro', OLD.id_livro,
            'titulo', OLD.titulo,
            'autor_id', OLD.autor_id,
            'isbn', OLD.isbn,
            'ano_publicacao', OLD.ano_publicacao,
            'genero_id', OLD.genero_id,
            'editora_id', OLD.editora_id,
            'quantidade_disponivel', OLD.quantidade_disponivel,
            'resumo', OLD.resumo
        ),
		JSON_OBJECT( -- DADOS ATUAIS
			'id_livro', NEW.id_livro,
            'titulo', NEW.titulo,
            'autor_id', NEW.autor_id,
            'isbn', NEW.isbn,
            'ano_publicacao', NEW.ano_publicacao,
            'genero_id', NEW.genero_id,
            'editora_id', NEW.editora_id,
            'quantidade_disponivel', NEW.quantidade_disponivel,
            'resumo', NEW.resumo
        )
    );
END;
// 

CREATE TRIGGER trg_log_delete_livro AFTER DELETE ON livros
FOR EACH ROW
BEGIN
    INSERT INTO logs(
        tabela,
        acao,
        registro_id,
        dados_antigos
    ) VALUES (
        'livros',
        'delete',
        OLD.id_livro,
        JSON_OBJECT( -- DADOS ANTIGOS
			'id_livro', OLD.id_livro,
            'titulo', OLD.titulo,
            'autor_id', OLD.autor_id,
            'isbn', OLD.isbn,
            'ano_publicacao', OLD.ano_publicacao,
            'genero_id', OLD.genero_id,
            'editora_id', OLD.editora_id,
            'quantidade_disponivel', OLD.quantidade_disponivel,
            'resumo', OLD.resumo
        )
    );
END;
// 

CREATE TRIGGER trg_log_update_autor AFTER UPDATE ON autores
FOR EACH ROW
BEGIN
    INSERT INTO logs(
        tabela,
        acao,
        registro_id,
        dados_antigos,
        dados_atuais
    ) VALUES (
        'autores',
        'update',
        NEW.id_autor,
        JSON_OBJECT( -- DADOS ANTIGOS
			'id_autor', OLD.id_autor,
            'nome_autor', OLD.nome_autor,
            'nacionalidade', OLD.nacionalidade,
            'data_nascimento', OLD.data_nascimento,
            'biografia', OLD.biografia
        ),
		JSON_OBJECT( -- DADOS ATUAIS
			'id_autor', NEW.id_autor,
            'nome_autor', NEW.nome_autor,
            'nacionalidade', NEW.nacionalidade,
            'data_nascimento', NEW.data_nascimento,
            'biografia', NEW.biografia
        )
    );
END;
// 

CREATE TRIGGER trg_log_delete_autor AFTER DELETE ON autores
FOR EACH ROW
BEGIN
    INSERT INTO logs(
        tabela,
        acao,
        registro_id,
        dados_antigos
    ) VALUES (
        'autores',
        'delete',
        OLD.id_autor,
        JSON_OBJECT( -- DADOS ANTIGOS
			'id_autor', OLD.id_autor,
            'nome_autor', OLD.nome_autor,
            'nacionalidade', OLD.nacionalidade,
            'data_nascimento', OLD.data_nascimento,
            'biografia', OLD.biografia
        )
    );
END;
// 

CREATE TRIGGER trg_log_update_editora AFTER UPDATE ON editoras
FOR EACH ROW
BEGIN
    INSERT INTO logs(
        tabela,
        acao,
        registro_id,
        dados_antigos,
        dados_atuais
    ) VALUES (
        'editoras',
        'update',
        NEW.id_editora,
        JSON_OBJECT( -- DADOS ANTIGOS
			'id_editora', OLD.id_editora,
            'nome_editora', OLD.nome_editora,
            'endereco_editora', OLD.endereco_editora
        ),
		JSON_OBJECT( -- DADOS ATUAIS
			'id_editora', NEW.id_editora,
            'nome_editora', NEW.nome_editora,
            'endereco_editora', NEW.endereco_editora
        )
    );
END;
// 

CREATE TRIGGER trg_log_delete_editora AFTER DELETE ON editoras
FOR EACH ROW
BEGIN
    INSERT INTO logs(
        tabela,
        acao,
        registro_id,
        dados_antigos
    ) VALUES (
        'editoras',
        'delete',
        OLD.id_editora,
        JSON_OBJECT( -- DADOS ANTIGOS
			'id_editora', OLD.id_editora,
            'nome_editora', OLD.nome_editora,
            'endereco_editora', OLD.endereco_editora
        )
    );
END;
// 