import mysql.connector
from datetime import date
from database.config import USER, HOST, PORT, DATABASE, PASSWORD, SQL_BASE, SQL_INSERTS, SQL_TRIGGERS
from werkzeug.security import generate_password_hash


def connect() -> mysql.connector.MySQLConnection:
    conn = mysql.connector.connect(
        user=USER, host=HOST, port=PORT, database=DATABASE, password=PASSWORD
    )

    return conn


# AVISO: NÃO CONSEGUIMOS RODAR O .SQL VIA EXECUTE, 
# FOI NECESSÁRIO COLOCAR O CODIGO DAS TRIGGERS AQUI MANUALMENTE
# PORQUE O MYSQL CONNECTOR NÃO SUPORTA O DELIMITER
# 👍
def createTriggers():
    triggers = [

        # ===============================
        # EMPRÉSTIMOS / LIVROS (PÓS-EVENTO)
        # ===============================

        """
        CREATE TRIGGER trg_repoe_livro
        AFTER UPDATE ON emprestimos
        FOR EACH ROW
        BEGIN
            IF NEW.status_emprestimo = 'devolvido' THEN
                UPDATE livros
                SET quantidade_disponivel = quantidade_disponivel + 1
                WHERE id_livro = OLD.livro_id;
            END IF;
        END
        """,

        """
        CREATE TRIGGER trg_tira_livro
        AFTER INSERT ON emprestimos
        FOR EACH ROW
        BEGIN
            UPDATE livros
            SET quantidade_disponivel = quantidade_disponivel - 1
            WHERE id_livro = NEW.livro_id;
        END
        """,

        """
        CREATE TRIGGER trg_repoe_livro_delete
        AFTER DELETE ON emprestimos
        FOR EACH ROW
        BEGIN
            IF OLD.status_emprestimo != 'devolvido' THEN
                UPDATE livros
                SET quantidade_disponivel = quantidade_disponivel + 1
                WHERE id_livro = OLD.livro_id;
            END IF;
        END
        """,

        """
        CREATE TRIGGER trg_multar
        AFTER UPDATE ON emprestimos
        FOR EACH ROW
        BEGIN
            DECLARE dias INT;
            IF OLD.status_emprestimo != 'devolvido'
               AND NEW.status_emprestimo = 'devolvido'
               AND CURRENT_DATE() > OLD.data_devolucao_prevista THEN
                SET dias = CURRENT_DATE() - OLD.data_devolucao_prevista;
                UPDATE usuarios
                SET multa_atual = multa_atual + (dias * 0.50)
                WHERE id_usuario = OLD.usuario_id;
            END IF;
        END
        """,

        """
        CREATE TRIGGER trg_descontar_multa
        AFTER UPDATE ON emprestimos
        FOR EACH ROW
        BEGIN
            DECLARE dias INT;
            IF OLD.status_emprestimo != 'devolvido'
               AND NEW.status_emprestimo = 'devolvido'
               AND CURRENT_DATE() < OLD.data_devolucao_prevista THEN
                SET dias = OLD.data_devolucao_prevista - CURRENT_DATE();
                UPDATE usuarios
                SET multa_atual = multa_atual - (dias * 0.05)
                WHERE id_usuario = OLD.usuario_id;
            END IF;
        END
        """,

        # ===============================
        # VALIDAÇÕES – LIVROS
        # ===============================

        """
        CREATE TRIGGER trg_corrige_quantidade_livro
        BEFORE INSERT ON livros
        FOR EACH ROW
        BEGIN
            IF NEW.quantidade_disponivel < 0 THEN
                SET NEW.quantidade_disponivel = 0;
            END IF;
        END
        """,

        """
        CREATE TRIGGER trg_corrige_isbn
        BEFORE INSERT ON livros
        FOR EACH ROW
        BEGIN
            IF LENGTH(NEW.isbn) < 13 THEN
                SET NEW.isbn = '0000000000000';
            END IF;
        END
        """,

        """
        CREATE TRIGGER trg_corrige_ano_publicacao_livro
        BEFORE INSERT ON livros
        FOR EACH ROW
        BEGIN
            IF NEW.ano_publicacao > YEAR(CURDATE()) THEN
                SET NEW.ano_publicacao = YEAR(CURDATE());
            END IF;
        END
        """,

        """
        CREATE TRIGGER trg_livros_titulo_validacao
        BEFORE INSERT ON livros
        FOR EACH ROW
        BEGIN
            SET NEW.titulo = TRIM(NEW.titulo);
            IF NEW.titulo = '' THEN
                SET NEW.titulo = 'TÍTULO NÃO INFORMADO';
            END IF;
        END
        """,

        """
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
        END
        """,

        # ===============================
        # USUÁRIOS
        # ===============================

        """
        CREATE TRIGGER trg_usuarios_multa_validacao
        BEFORE INSERT ON usuarios
        FOR EACH ROW
        BEGIN
            IF NEW.multa_atual < 0 THEN
                SET NEW.multa_atual = 0;
            END IF;
        END
        """,

        """
        CREATE TRIGGER trg_auto_data_inscricao
        BEFORE INSERT ON usuarios
        FOR EACH ROW
        BEGIN
            IF NEW.data_inscricao IS NULL THEN
                SET NEW.data_inscricao = CURDATE();
            END IF;
        END
        """,

        """
        CREATE TRIGGER trg_auto_multa_padrao
        BEFORE INSERT ON usuarios
        FOR EACH ROW
        BEGIN
            IF NEW.multa_atual IS NULL THEN
                SET NEW.multa_atual = 0;
            END IF;
        END
        """,

        # ===============================
        # EMPRÉSTIMOS – AUTOMAÇÕES
        # ===============================

        """
        CREATE TRIGGER trg_auto_status_emprestimo
        BEFORE INSERT ON emprestimos
        FOR EACH ROW
        BEGIN
            IF NEW.status_emprestimo IS NULL THEN
                SET NEW.status_emprestimo = 'pendente';
            END IF;
        END
        """,

        """
        CREATE TRIGGER trg_auto_data_devolucao_prevista
        BEFORE INSERT ON emprestimos
        FOR EACH ROW
        BEGIN
            IF NEW.data_devolucao_prevista IS NULL THEN
                SET NEW.data_devolucao_prevista =
                    DATE_ADD(NEW.data_emprestimo, INTERVAL 7 DAY);
            END IF;
        END
        """,

        # ===============================
        # AUDITORIA – LIVROS
        # ===============================

        """
        CREATE TRIGGER trg_log_update_livro
        AFTER UPDATE ON livros
        FOR EACH ROW
        BEGIN
            INSERT INTO logs (tabela, acao, registro_id, dados_antigos, dados_atuais)
            VALUES (
                'livros',
                'update',
                NEW.id_livro,
                JSON_OBJECT(
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
                JSON_OBJECT(
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
        END
        """,

        """
        CREATE TRIGGER trg_log_delete_livro
        AFTER DELETE ON livros
        FOR EACH ROW
        BEGIN
            INSERT INTO logs (tabela, acao, registro_id, dados_antigos)
            VALUES (
                'livros',
                'delete',
                OLD.id_livro,
                JSON_OBJECT(
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
        END
        """,

        # ===============================
        # AUDITORIA – AUTORES
        # ===============================

        """
        CREATE TRIGGER trg_log_update_autor
        AFTER UPDATE ON autores
        FOR EACH ROW
        BEGIN
            INSERT INTO logs (tabela, acao, registro_id, dados_antigos, dados_atuais)
            VALUES (
                'autores',
                'update',
                NEW.id_autor,
                JSON_OBJECT(
                    'id_autor', OLD.id_autor,
                    'nome_autor', OLD.nome_autor,
                    'nacionalidade', OLD.nacionalidade,
                    'data_nascimento', OLD.data_nascimento,
                    'biografia', OLD.biografia
                ),
                JSON_OBJECT(
                    'id_autor', NEW.id_autor,
                    'nome_autor', NEW.nome_autor,
                    'nacionalidade', NEW.nacionalidade,
                    'data_nascimento', NEW.data_nascimento,
                    'biografia', NEW.biografia
                )
            );
        END
        """,

        """
        CREATE TRIGGER trg_log_delete_autor
        AFTER DELETE ON autores
        FOR EACH ROW
        BEGIN
            INSERT INTO logs (tabela, acao, registro_id, dados_antigos)
            VALUES (
                'autores',
                'delete',
                OLD.id_autor,
                JSON_OBJECT(
                    'id_autor', OLD.id_autor,
                    'nome_autor', OLD.nome_autor,
                    'nacionalidade', OLD.nacionalidade,
                    'data_nascimento', OLD.data_nascimento,
                    'biografia', OLD.biografia
                )
            );
        END
        """,

        # ===============================
        # AUDITORIA – EDITORAS
        # ===============================

        """
        CREATE TRIGGER trg_log_update_editora
        AFTER UPDATE ON editoras
        FOR EACH ROW
        BEGIN
            INSERT INTO logs (tabela, acao, registro_id, dados_antigos, dados_atuais)
            VALUES (
                'editoras',
                'update',
                NEW.id_editora,
                JSON_OBJECT(
                    'id_editora', OLD.id_editora,
                    'nome_editora', OLD.nome_editora,
                    'endereco_editora', OLD.endereco_editora
                ),
                JSON_OBJECT(
                    'id_editora', NEW.id_editora,
                    'nome_editora', NEW.nome_editora,
                    'endereco_editora', NEW.endereco_editora
                )
            );
        END
        """,

        """
        CREATE TRIGGER trg_log_delete_editora
        AFTER DELETE ON editoras
        FOR EACH ROW
        BEGIN
            INSERT INTO logs (tabela, acao, registro_id, dados_antigos)
            VALUES (
                'editoras',
                'delete',
                OLD.id_editora,
                JSON_OBJECT(
                    'id_editora', OLD.id_editora,
                    'nome_editora', OLD.nome_editora,
                    'endereco_editora', OLD.endereco_editora
                )
            );
        END
        """
    ]

    conn = connect()
    cursor = conn.cursor()

    for trigger in triggers:
        cursor.execute(trigger)

    conn.commit()
    cursor.close()



def initDB():
    try:
        conn = connect()
        conn.close()
    except:
        conn = mysql.connector.connect(
            user=USER, host=HOST, port=PORT, password=PASSWORD
        )

        cur = conn.cursor()
        with open(SQL_BASE, "r") as base:
            cur.execute(base.read())
        cur.close()

        conn.close()


        pswd_hash = generate_password_hash('admin')

        initBooks()
        addUser(nome='admin', email='admin@admin', senha_hash=pswd_hash, admin=True)
        
        createTriggers()


def initBooks():
    conn = connect()
    cur = conn.cursor()

    with open(SQL_INSERTS, "r", encoding="utf-8") as inserts:
        sql = inserts.read()

    for query in sql.split(";"):
        # print('+'*40)
        # print(query)
        # print(query.strip())
        if query.strip():
            cur.execute(query.strip())

    conn.commit()
    cur.close()
    conn.close()


def getBooks():
    query = """
        SELECT 
            l.*,
            g.nome_genero,
            a.nome_autor,
            e.nome_editora
        FROM livros l
        INNER JOIN generos g
            ON l.genero_id = g.id_genero
        INNER JOIN autores a
            ON l.autor_id = a.id_autor
        INNER JOIN editoras e
            ON l.editora_id = e.id_editora
    """
    with connect() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(query)
        livros = cur.fetchall()
        cur.close()
    return livros


def addUserBook(user_id, book_id):
    user_id = int(user_id)
    book_id = int(book_id)

    data_emprestimo = date.today()

    if data_emprestimo.day + 7 > 31:
        devolucao_prevista = date(
            data_emprestimo.year,
            data_emprestimo.month + 1,
            data_emprestimo.day + 7 - 31,
        )
    else:
        devolucao_prevista = date(
            data_emprestimo.year, data_emprestimo.month, data_emprestimo.day + 7
        )

    data_emprestimo = data_emprestimo

    query = """
        INSERT INTO emprestimos (usuario_id, livro_id, data_emprestimo, data_devolucao_prevista, status_emprestimo) 
        VALUES(
            %s,
            %s,
            %s,
            %s,
            %s
        )
    """
    with connect() as conn:
        cur = conn.cursor()
        cur.execute(
            query, (user_id, book_id, data_emprestimo, devolucao_prevista, "pendente")
        )
        conn.commit()
        cur.close()


    query = """
        UPDATE livros SET quantidade_disponivel = quantidade_disponivel - 1 WHERE id_livro = %s;
    """
    with connect() as conn:
        cur = conn.cursor()
        cur.execute(
            query, (book_id,)
        )
        conn.commit()
        cur.close()


def getUserBooks(user_id):
    query = """
        SELECT 
            l.*,
            ep.*,
            g.nome_genero,
            a.nome_autor,
            e.nome_editora
        FROM usuarios u
        INNER JOIN emprestimos ep
            ON u.id_usuario = ep.usuario_id
        INNER JOIN livros l
            ON l.id_livro = ep.livro_id

        INNER JOIN generos g
            ON l.genero_id = g.id_genero
        INNER JOIN autores a
            ON l.autor_id = a.id_autor
        INNER JOIN editoras e
            ON l.editora_id = e.id_editora
        WHERE u.id_usuario = %s
        ORDER BY FIELD(status_emprestimo, 'atrasado', 'pendente','devolvido')
    """
    with connect() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(query, (user_id,))
        livros = cur.fetchall()
        cur.close()
    return livros

def getEmprestimos():
    query = """
        SELECT 
            *
        FROM emprestimos
    """
    with connect() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(query)
        livros = cur.fetchall()
        cur.close()
    return livros

def returnBook(emprestimo_id):
    # depois fazer adicionar na multa se estiver atrasado
    data_devolucao = date.today()

    query = """
        UPDATE emprestimos
        SET 
            status_emprestimo='devolvido',
            data_devolucao_real=%s
        WHERE id_emprestimo=%s
    """

    with connect() as conn:
        cur = conn.cursor()
        cur.execute(query, (data_devolucao, emprestimo_id))
        conn.commit()
        cur.close()

    query = """
        SELECT livro_id 
        FROM emprestimos
        WHERE id_emprestimo = %s
    """

    with connect() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(query, (emprestimo_id,))
        book_id = cur.fetchone()["livro_id"]
        cur.close()

    query = """
        UPDATE livros SET quantidade_disponivel = quantidade_disponivel + 1 WHERE id_livro = %s;
    """
    with connect() as conn:
        cur = conn.cursor()
        cur.execute(
            query, (book_id,)
        )
        conn.commit()
        cur.close()


def addUser(nome, email, senha_hash, numero = None, admin = False):
    conn = connect()
    cur = conn.cursor()

    adduser = """
        INSERT INTO usuarios (nome_usuario, email, numero_telefone, senha_hash, data_inscricao, admin)
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    data = date.today()

    usuario = (nome, email, numero, senha_hash, data, admin)

    cur.execute(adduser, usuario)

    conn.commit()
    cur.close()
    conn.close()


def getUserById(id):
    conn = connect()
    cur = conn.cursor(dictionary=True)

    query = """
        SELECT *
        FROM usuarios
        WHERE id_usuario = %s
    """

    cur.execute(query, (id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user


def getUserByEmail(email):
    conn = connect()
    cur = conn.cursor(dictionary=True)

    query = """
        SELECT *
        FROM usuarios
        WHERE email = %s
    """

    cur.execute(query, (email,))
    user = cur.fetchone()

    cur.close()
    conn.close()
    return user

def addAuthor(nome, nacionalidade, data_nascimento, biografia):
    query = '''
        INSERT INTO autores(nome_autor, nacionalidade, data_nascimento, biografia) VALUES
        (%s, %s, %s, %s)

    '''
    params = (nome, nacionalidade, data_nascimento, biografia)

    with connect() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        cur.close()     

def getAuthors():
    query = '''SELECT * FROM autores'''

    with connect() as conn:
        cur = conn.cursor(dictionary=True)

        cur.execute(query)
        results = cur.fetchall()
        
        cur.close()     
    return results

def addBook(titulo, autor_id, isbn, ano_publicacao, genero_id, editora_id, quantidade_disponivel, resumo):
    query = '''
        INSERT INTO livros(titulo, autor_id, isbn, ano_publicacao, genero_id, editora_id, quantidade_disponivel, resumo) VALUES
        (%s, %s, %s, %s, %s, %s, %s, %s)

    '''
    params = (titulo, autor_id, isbn, ano_publicacao, genero_id, editora_id, quantidade_disponivel, resumo)

    with connect() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        cur.close()

def addPublisher(nome, endereco):
    query = '''
        INSERT INTO editoras(nome_editora, endereco_editora) VALUES
        (%s, %s)

    '''
    params = (nome, endereco)

    with connect() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        cur.close()

def getPublishers():
    query = '''SELECT * FROM editoras'''

    with connect() as conn:
        cur = conn.cursor(dictionary=True)

        cur.execute(query)
        results = cur.fetchall()
        
        cur.close()     
    return results


def getGenres():
    query = '''SELECT * FROM generos'''

    with connect() as conn:
        cur = conn.cursor(dictionary=True)

        cur.execute(query)
        results = cur.fetchall()
        
        cur.close()     
    return results

def deleteBook(id):
    query = '''
        DELETE FROM livros
        WHERE id_livro = %s
    '''

    params = (id,)

    with connect() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        cur.close()

def deleteAuthor(id):
    query = '''
        DELETE FROM autores
        WHERE id_autor = %s
    '''

    params = (id,)

    with connect() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        cur.close()

def deletePublisher(id):
    query = '''
        DELETE FROM editoras
        WHERE id_editora = %s
    '''

    params = (id,)

    with connect() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        cur.close()


def getPublisherById(id):
    conn = connect()
    cur = conn.cursor(dictionary=True)

    query = """
        SELECT *
        FROM editoras
        WHERE id_editora = %s
    """

    cur.execute(query, (id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result

def getAuthorById(id):
    conn = connect()
    cur = conn.cursor(dictionary=True)

    query = """
        SELECT *
        FROM autores
        WHERE id_autor = %s
    """

    cur.execute(query, (id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result

def getBookById(id):
    conn = connect()
    cur = conn.cursor(dictionary=True)

    query = """
        SELECT *
        FROM livros
        WHERE id_livro = %s
    """

    cur.execute(query, (id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result


def updateBook(id_livro, titulo, autor_id, isbn, ano_publicacao, genero_id, editora_id, quantidade_disponivel, resumo):
    query = '''
        UPDATE livros
        SET titulo=%s, autor_id=%s, isbn=%s, ano_publicacao=%s, genero_id=%s, editora_id=%s, quantidade_disponivel=%s, resumo=%s
        WHERE id_livro = %s
    '''
    
    params = (
        titulo, 
        autor_id, 
        isbn, 
        ano_publicacao, 
        genero_id, 
        editora_id, 
        quantidade_disponivel, 
        resumo, 
        id_livro
    )

    with connect() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        cur.close()

def updateAuthor(id_autor, nome_autor, nacionalidade, data_nascimento, biografia):
    query = '''
        UPDATE autores
        SET nome_autor=%s, nacionalidade=%s, data_nascimento=%s, biografia=%s
        WHERE id_autor = %s
    '''
    
    params = (
        nome_autor,
        nacionalidade, 
        data_nascimento, 
        biografia,
        id_autor
    )

    with connect() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        cur.close()

def updatePublisher(id_editora, nome_editora, endereco_editora):
    query = '''
        UPDATE editoras
        SET nome_editora=%s, endereco_editora=%s
        WHERE id_editora = %s
    '''
    
    params = (
        nome_editora, 
        endereco_editora,
        id_editora
    )

    with connect() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        cur.close()