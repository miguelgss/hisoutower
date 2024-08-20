import psycopg2
import re
import traceback
from datetime import datetime, timedelta
from Utils import Mensagens, Cores, Gerador
from .DataTransferObjects import DBResultado

from DomainGeneral import GerarFichaDTO, JogadorInputDTO

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

    async def ObterPerfil(self, discordUser:JogadorInputDTO ):
        Retorno = DBResultado()
        try:
            conn = psycopg2.connect(self.connectionString)
            cur = conn.cursor()

            cur.execute(f"""
                    SELECT 
                        u.nome as usuario,
                        r.power,  
                        u.pontos,
                        p.nome as corpo, 
                        p2.nome as borda_corpo
                    FROM usuario u
                    JOIN ranqueamento r on id_usuario = u.id
                    JOIN ficha f on f.id_usuario = u.id
                    LEFT JOIN produto p on p.id = f.id_corpo
                    LEFT JOIN produto p2 on (f.id_borda_corpo is null and p2.id is null) or f.id_borda_corpo = p2.id
                    WHERE u.discord_id_user = '{discordUser.IdDiscord}' 
                    """)
            jogador = cur.fetchone()
            
            if(jogador == None):
                cur.close()
                conn.close()
                Retorno.resultado = Mensagens.UsuarioNaoEncontrado
                Retorno.corResultado = Cores.Erro
                return Retorno
            
            cur.execute(f"""
                SELECT id, nome from andar where min_points <= {jogador[1]} order by min_points desc limit 1; 
            """)

            andarAtual = cur.fetchone()

            inputDadosFicha = GerarFichaDTO()
            inputDadosFicha.Avatar = discordUser.Avatar
            inputDadosFicha.Nome = discordUser.Nome
            inputDadosFicha.IdAndar = andarAtual[0]
            inputDadosFicha.NomeAndar = andarAtual[1]
            inputDadosFicha.Power = jogador[1]
            inputDadosFicha.Pontos = jogador[2]
            inputDadosFicha.TipoCorpo = jogador[3]
            inputDadosFicha.TipoBordaCorpo = jogador[4]

            Retorno.arquivo = await Gerador.GerarCardPerfil(inputDadosFicha)            
            Retorno.corResultado = Cores.Sucesso
            
            cur.close()
            conn.close()
            return Retorno

        except Exception as e:
            cur.close()
            conn.close()
            Retorno.resultado += "Ocorreu um erro: \n" + str(traceback.format_exc())
            Retorno.corResultado = Cores.Erro
        return Retorno
        
