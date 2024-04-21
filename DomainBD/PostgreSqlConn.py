import psycopg2
import re
import traceback
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

    async def ObterPerfil(self, discordUser, tipoFicha:str):
        Retorno = DBResultado()
        tipoFicha = tipoFicha.lower()
        try:
            conn = psycopg2.connect(self.connectionString)
            cur = conn.cursor()

            cur.execute(f"""
                    SELECT a.id, r.partidas_para_subir, r.partidas_para_descer, usuario.tipo_ficha
                    FROM usuario
                    JOIN ranqueamento r on id_usuario = usuario.id  
                    JOIN andar a on a.id = r.id_andar_atual 
                    WHERE usuario.discord_id_user = '{discordUser.id}' 
                    """)
            jogador = cur.fetchone()
            
            if(jogador == None):
                cur.close()
                conn.close()
                Retorno.resultado = Mensagens.UsuarioNaoEncontrado
                Retorno.corResultado = Cores.Erro
                return Retorno

            andarAtual = Mensagens.LISTA_ICONES_ANDARES[jogador[0] - 1]
            if(tipoFicha in Mensagens.LISTA_FICHA_PERSONAGENS):
                if(tipoFicha != jogador[3]):
                    cur.execute(f"""
                        UPDATE usuario SET
                            tipo_ficha = '{tipoFicha}'
                            WHERE discord_id_user = '{discordUser.id}';
                        """)

                    cur.execute(f"""
                        SELECT a.id, r.partidas_para_subir, r.partidas_para_descer, usuario.tipo_ficha
                        FROM usuario
                        JOIN ranqueamento r on id_usuario = usuario.id  
                        JOIN andar a on a.id = r.id_andar_atual 
                        WHERE usuario.discord_id_user = '{discordUser.id}' 
                        """)
                    jogador = cur.fetchone()
                    conn.commit()
                Retorno.arquivo = await Gerador.GerarCardPerfil(discordUser, jogador[3], andarAtual, jogador[1] < 2, jogador[2] < 2)            
                Retorno.corResultado = Cores.Sucesso
            elif(tipoFicha == ''):
                Retorno.arquivo = await Gerador.GerarCardPerfil(discordUser, jogador[3], andarAtual, jogador[1] < 2, jogador[2] < 2)            
                Retorno.corResultado = Cores.Sucesso
            else:
                Retorno.resultado = f"Não foi possível achar o tipo de ficha informado. Tente algum dos seguintes nomes: {Mensagens.LISTA_FICHA_PERSONAGENS}"
                Retorno.corResultado = Cores.Alerta
            
            cur.close()
            conn.close()
            return Retorno

        except Exception as e:
            cur.close()
            conn.close()
            Retorno.resultado += "Ocorreu um erro: \n" + str(traceback.format_exc())
            Retorno.corResultado = Cores.Erro
        return Retorno
        
