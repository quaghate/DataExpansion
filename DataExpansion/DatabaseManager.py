from mysql.connector.pooling import MySQLConnectionPool
import psycopg2
import psycopg2.pool as pool
import sqlite3
import os
import mysql.connector
class DatabaseManager:
    """Classe base abstrata para gerenciamento de bancos de dados."""

    def __init__(self, **kwargs):
        """Inicializa o gerenciador de banco de dados.""" 
        raise NotImplementedError("Subclasses devem implementar __init__")

    def connect(self):
        """Conecta ao banco de dados."""
        raise NotImplementedError("Subclasses devem implementar connect")

    def close(self):
        """Fecha a conexão com o banco de dados."""
        raise NotImplementedError("Subclasses devem implementar close")

    def carregar_dados(self, nome_tabela):
        """Carrega dados de uma tabela específica."""
        raise NotImplementedError("Subclasses devem implementar carregar_dados")

    def descartar_banco_temporario(self, nome_banco):
        """Descarta um banco de dados temporário."""
        raise NotImplementedError("Subclasses devem implementar descartar_banco_temporario")

    def criar_banco_de_dados(self, nome_banco):
        """Cria um novo banco de dados."""
        raise NotImplementedError("Subclasses devem implementar criar_banco_de_dados")

    def salvar_dados(self, dados, nome_tabela):
        """Salva dados em uma tabela específica."""
        raise NotImplementedError("Subclasses devem implementar salvar_dados")

class MySQLManager(DatabaseManager):
    """Gerenciador de banco de dados MySQL."""

    def __init__(self, localizacao_banco, host, user, password, pool_size=3):
        """Inicializa o gerenciador de banco de dados MySQL."""
        super().__init__(localizacao_banco)
        self.host = host
        self.user = user
        self.password = password
        self.database = localizacao_banco #  localizacao_banco é o nome do banco
        self.pool_size = pool_size
        self.connection_pool = None
        self.criar_banco_de_dados() # Cria o banco se não existir
        self.connect()

    def connect(self):
        """Conecta ao banco de dados MySQL."""
        try:
            self.connection_pool = MySQLConnectionPool(
                pool_name="MySQL_pool",
                pool_size=self.pool_size,
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database, # Conecta ao banco especificado
            )
            print(f"Conexão MySQL estabelecida com sucesso! Banco: {self.database}")
        except mysql.connector.Error as err: # Captura exceção específica
            print(f"Erro ao conectar ao MySQL: {err}")
            # Trate o erro adequadamente (re-lançar, logar, sair, etc.)

    def close(self):
        """Fecha a conexão com o banco de dados MySQL."""
        if self.connection_pool:
            self.connection_pool.close()
            print(f"Conexão MySQL fechada. Banco: {self.database}")


    def carregar_dados(self, nome_tabela):
        """Carrega dados de uma tabela específica no MySQL."""
        try:
            connection = self.connection_pool.get_connection()
            cursor = connection.cursor(dictionary=True) # Use dictionary=True para resultados como dicionários
            cursor.execute(f"SELECT * FROM {nome_tabela}")
            dados = cursor.fetchall()
            return dados
        except mysql.connector.Error as err:
            print(f"Erro ao carregar dados do MySQL: {err}")
            return None
        finally:
            if connection:
                cursor.close()
                self.connection_pool.put_connection(connection)

    def descartar_banco_temporario(self, nome_banco):
        """Descarta um banco de dados temporário no MySQL."""
        try:
            connection = self.connection_pool.get_connection()
            cursor = connection.cursor()
            cursor.execute("DROP DATABASE IF EXISTS %s", (nome_banco,)) # Usando parâmetros
            connection.commit()
            print(f"Banco de dados temporário '{nome_banco}' removido.")
        except mysql.connector.Error as err:
            print(f"Erro ao remover banco de dados: {err}")
        finally:
            if connection:
                cursor.close()
                self.connection_pool.put_connection(connection)

    def criar_banco_de_dados(self): # Não recebe nome, pois usa self.localizacao_banco
        """Cria o banco de dados se não existir."""
        try:
            # Conexão temporária com privilégios de administrador
            temp_connection = MySQLConnectionPool(pool_name="temp_pool", pool_size=1, host=self.host, user=self.user, password=self.password) 
            cursor = temp_connection.get_connection().cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.localizacao_banco}") 
            # ... (GRANT privileges se necessário) ...

        except mysql.connector.Error as err:
            print(f"Erro ao criar o banco de dados MySQL: {err}")
        finally:
            if temp_connection:
                 temp_connection.close()

        def salvar_dados(self, dados, nome_tabela):
            """Salva dados em uma tabela específica no MySQL."""
            try:
                connection = self.connection_pool.get_connection()
                cursor = connection.cursor()
    
                for linha in dados:
                    colunas = ', '.join(linha.keys())
                    placeholders = ', '.join(['%s'] * len(linha))
                    valores = tuple(linha.values())
    
                    sql = f"INSERT INTO {nome_tabela} ({colunas}) VALUES ({placeholders})"
                    cursor.execute(sql, valores)  # Executa com parâmetros
    
                connection.commit()
                print(f"Dados salvos na tabela '{nome_tabela}' do MySQL com sucesso!")
    
            except mysql.connector.Error as err:  # Trata exceções do MySQL
                print(f"Erro ao salvar dados no MySQL: {err}")
                # Aqui você pode adicionar lógica para lidar com o erro específico
                # Exemplos: rollback da transação, log do erro, etc.
                # Se o erro for crítico, você pode re-lançar a exceção:
                # raise err
    
            finally:
                if connection:
                    cursor.close()
                    self.connection_pool.put_connection(connection)
    
class SQLiteManager(DatabaseManager):
    """Gerenciador de banco de dados SQLite."""

    def __init__(self, db_path):
        """Inicializa o gerenciador de banco de dados SQLite."""
        self.db_path = db_path
        self.connection = None

    def connect(self):
        """Conecta ao banco de dados SQLite."""
        try:
            self.connection = sqlite3.connect(self.db_path)
            print(f"Conexão com o banco de dados SQLite '{self.db_path}' estabelecida com sucesso!")
            # Habilitar chaves estrangeiras
            self.connection.execute("PRAGMA foreign_keys = ON;")
            return self.connection # Retorna a conexão para ser usada em transações
        except sqlite3.Error as e:
            print(f"Erro ao conectar ao banco de dados SQLite: {e}")
            return None # Retorna None em caso de erro


    def close(self):
        """Fecha a conexão com o banco de dados SQLite."""
        if self.connection:
            self.connection.close()
            print(f"Conexão com o banco de dados SQLite '{self.db_path}' fechada.")

    def carregar_dados(self, nome_tabela, colunas="*", where=None):  # Adiciona parâmetros opcionais
        """Carrega dados de uma tabela específica no SQLite."""
        try:
            cursor = self.connection.cursor()
            query = f"SELECT {colunas} FROM {nome_tabela}"
            if where:
                query += f" WHERE {where}" # Adiciona cláusula WHERE se fornecida
            cursor.execute(query)
            dados = cursor.fetchall()
            return dados
        except sqlite3.Error as e:
            print(f"Erro ao carregar dados do SQLite: {e}")
            return None

    def descartar_banco_temporario(self, db_path=None):  # Permite especificar o caminho
        """Descarta um banco de dados temporário no SQLite."""
        if db_path is None:
            db_path = self.db_path  # Usa o caminho padrão se não for especificado
        try:
            if os.path.exists(db_path):
                self.close()  # Fechar a conexão antes de excluir o arquivo
                os.remove(db_path)
                print(f"Banco de dados SQLite temporário '{db_path}' removido com sucesso.")
            else:
                print(f"O banco de dados '{db_path}' não existe.") # Mensagem mais informativa
        except OSError as e:
            print(f"Erro ao remover o banco de dados SQLite temporário '{db_path}': {e}")

    def criar_banco_de_dados(self):
        """Cria as tabelas necessárias no banco de dados SQLite se elas não existirem."""
        try:
            cursor = self.connection.cursor()
            # Adicionar suas queries CREATE TABLE aqui, com chaves estrangeiras se necessário
            # Exemplo:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    email TEXT UNIQUE
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS produtos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    usuario_id INTEGER,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                )
            ''')


            self.connection.commit()
            print(f"Tabelas criadas com sucesso no banco de dados SQLite '{self.db_path}'.")
        except sqlite3.Error as e:
            print(f"Erro ao criar as tabelas no banco de dados SQLite: {e}")


    def salvar_dados(self, dados, nome_tabela):
        """Salva dados em uma tabela específica no SQLite."""
        try:
            cursor = self.connection.cursor()

            for linha in dados:
                colunas = ', '.join(linha.keys())
                placeholders = ', '.join(['?'] * len(linha))
                valores = tuple(linha.values())

                sql = f"INSERT INTO {nome_tabela} ({colunas}) VALUES ({placeholders})"
                cursor.execute(sql, valores)

            self.connection.commit()
            print(f"Dados salvos na tabela '{nome_tabela}' do SQLite com sucesso!")
        except sqlite3.Error as e:
            print(f"Erro ao salvar dados no SQLite: {e}")

class DatabaseFactory:
    @staticmethod
    def create_database_manager(db_type, **kwargs):
        if db_type == "mysql":
            return MySQLManager(**kwargs)  # kwargs: host, user, password, database, pool_size
        elif db_type == "sqlite":
            return SQLiteManager(**kwargs) # kwargs: db_path
        # Adicione outros tipos de banco de dados aqui se necessário (PostgreSQL, etc.)
        else:
            raise ValueError("Tipo de banco de dados inválido.")