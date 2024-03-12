import psycopg2
import re
from datetime import datetime, timedelta
from Utils import Mensagens, Cores, Gerador

class PostgreSqlConn():
    def __init__(self):
        DBNAME = ''
        USER = ''
        with open('sqlsettings.txt') as f:
            for line in f:
                if re.search("dbname", line):
                    DBNAME = line.split(' ')[2]
                if re.search("user", line):
                    USER = line.split(' ')[2]
        self.connectionString = f"dbname={DBNAME} user={USER}"

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

    
    
    ### - DESAFIOS

    
    ### - DADOS BUSCA - TABELAS DE DOMÍNIO

    

    ### - ROTINAS TASK
    
    # def RegistrarAndar(Andar):
    #     Retorno = DBResultado()
    #     pesquisa = None
    #     conn = psycopg2.connect(self.connectionString)
    #     cur = conn.cursor()
    #     try:
    #         cur.execute(f"""select id from temporada order by temporada.id desc""")
    #         pesquisa = cur.fetchone
            
    #         if(pesquisa != None):
    #             cur.execute(f"""
    #                 insert into andar (nome, data_criacao,id_temporada)
    #                 select '{Andar}', '{datetime.now()}, {pesquisa[0]}'
    #                 where not exists(
    #                     select nome from andar where nome = '{Andar}' 
    #                     and id_temporada = '{pesquisa[0]}'
    #                     );
    #             """)
    #             Retorno.pesquisa = f"{Andar} foi registrado para a temporada {pesquisa[0]}!"
    #         else:
    #             Retorno.pesquisa = "Parece que ainda não há uma temporada registradas."

    #         conn.commit()
    #         cur.close()
    #         conn.close()

    #         Retorno.corResultado = Cores.Sucesso
    #     except Exception as e:
    #         cur.close()
    #         conn.close()
    #         Retorno.pesquisa += "Ocorreu um erro: \n" + str(e)
    #         Retorno.corResultado = Cores.Erro
            
    #     return Retorno
        