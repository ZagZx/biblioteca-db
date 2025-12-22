DELIMITER //
-- Pós evento
CREATE TRIGGER trg_repoe_livro AFTER UPDATE 
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

-- triggers validação
-- Impedir quantidade negativa de livros
DELIMITER //

create trigger trg_corrige_quantidade_livro
before insert on livros
for each row
begin
    if NEW.quantidade_disponivel < 0 then
        set NEW.quantidade_disponivel = 0;
    end if;
end//

DELIMITER ;

-- Ajustar ISBN com tamanho diferente de 13 (se não tiver 13 caracteres , ele vira 0)
DELIMITER //

create trigger trg_corrige_isbn
before insert on livros
for each row
begin
    if length(NEW.isbn) < 13 then 
        set NEW.isbn = '0000000000000';
    end if;
end//

DELIMITER ;

-- Ajustar data futura (se estiver no futuro coloque na data atual)
DELIMITER //

create trigger trg_corrige_ano_publicacao_livro
before insert on livros
for each row
begin
    if NEW.ano_publicacao > year(curdate()) then
        set NEW.ano_publicacao = year(curdate());
    end if;
    
end//

DELIMITER ;

-- Impedir títulos de livros vazios
DELIMITER //

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

DELIMITER ;

-- Impedir multa negativa do usuário
DELIMITER //

create trigger trg_usuarios_multa_validacao
before insert on usuarios
for each row
begin
    if NEW.multa_atual < 0 then
        set NEW.multa_atual = 0;
    end if;
end;
//

DELIMITER ;

-- Geração Automática de Valores


-- Define automaticamente o status do empréstimo como "pendente"
-- Caso o status não seja informado pelo sistema ou usuário

DELIMITER //

CREATE TRIGGER trg_auto_status_emprestimo
BEFORE INSERT ON emprestimos
FOR each ROW
BEGIN
    IF new.status_emprestimo IS NULL THEN
        SET new.status_emprestimo = 'pendente';
    END IF;
END;
//

DELIMITER ;


-- Preenche automaticamente a data de inscrição do usuário
-- Caso a data não seja informada no momento do cadastro

DELIMITER //

CREATE TRIGGER trg_auto_data_inscricao
BEFORE INSERT ON usuarios
FOR each ROW
BEGIN
    IF NEW.data_inscricao IS NULL THEN
        SET NEW.data_inscricao = CURDATE();
    END IF;
END;
//

DELIMITER ;


-- Gera automaticamente a data de devolução prevista
-- Considera 7 dias após a data do empréstimo, se não for informada

DELIMITER //

CREATE TRIGGER trg_auto_data_devolucao_prevista
BEFORE INSERT ON emprestimos
FOR EACH ROW
BEGIN
    IF NEW.data_devolucao_prevista IS NULL THEN
        SET NEW.data_devolucao_prevista = DATE_ADD(NEW.data_emprestimo, INTERVAL 7 DAY);
    END IF;
END;
//

DELIMITER ;


-- Define automaticamente o valor inicial da multa do usuário
-- Evita valores nulos no cadastro de novos usuários

DELIMITER //

CREATE TRIGGER trg_auto_multa_padrao
BEFORE INSERT ON usuarios
FOR EACH ROW
BEGIN
    IF NEW.multa_atual IS NULL THEN
        SET NEW.multa_atual = 0;
    END IF;
END;
//

DELIMITER ;



-- Gera automaticamente um resumo padrão para o livro
-- Caso o campo resumo não seja preenchido no cadastro

DELIMITER //

CREATE TRIGGER trg_auto_resumo_livro
BEFORE INSERT ON livros
FOR EACH ROW
BEGIN
    IF NEW.resumo IS NULL OR NEW.resumo = '' THEN
        SET NEW.resumo = CONCAT(
            'Livro "', NEW.titulo,
            '" cadastrado automaticamente no sistema.'
        );
    END IF;
END;
//


DELIMITER ;