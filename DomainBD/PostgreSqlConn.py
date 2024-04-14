import psycopg2
import re
from datetime import datetime, timedelta
from Utils import Mensagens, Cores, Gerador
from .DataTransferObjects import DBResultado

class PostgreSqlConn():
    def __init__(self):
        DBNAME = ''
        USER = ''
        PORT = ''
        PASSWORD = ''
        HOST = ''

        with open('sqlsettings.txt') as f:
            for line in f:
                if re.search("dbname", line):
                    DBNAME = line.split(' ')[2]
                elif re.search("user", line):
                    USER = line.split(' ')[2]
                elif re.search("port", line):
                    PORT = line.split(' ')[2]
                elif re.search("password", line):
                    PASSWORD = line.split(' ')[2]
                elif re.search("host", line):
                    HOST = line.split(' ')[2]
        
        self.connectionString = f'user={USER} password={PASSWORD} host={HOST} port={PORT} dbname={DBNAME}'

    def TestConnection(self):
        Retorno = DBResultado()
        try:
            conn = psycopg2.connect(self.connectionString)
            cur = conn.cursor()

            cur.execute("CREATE TABLE test (id serial PRIMARY KEY, num integer, data varchar);")
            cur.execute("INSERT INTO test (num, data) VALUES (%s, %s)",(100, "abc'def"))
            cur.execute("SELECT * FROM test;")

            cur.close()
            conn.rollback()
            conn.close()

            Retorno.resultado = "Conexão funcionando!"
            Retorno.corResultado = Cores.Sucesso
        except Exception as e:
            Retorno.resultado += "Ocorreu um erro: \n" + str(e)
            Retorno.corResultado = Cores.Erro

        return Retorno
        
