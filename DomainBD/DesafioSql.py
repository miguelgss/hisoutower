import psycopg2
from datetime import datetime, timedelta
from Utils import Mensagens, Cores, Gerador

from .PostgreSqlConn import PostgreSqlConn
from .DataTransferObjects import DBResultado
from .TabelasDominioSql import TabelasDominioSql

class DesafioSql(PostgreSqlConn):
    def __init__(self):
        super(DesafioSql, self).__init__()
        self.tabelasDominioDB = TabelasDominioSql()

    def Desafiar(self, IdDiscordDesafiante, IdDiscordDesafiado):
        Retorno = DBResultado()
        jogadores = []
        dataAtual = datetime.now()
        dataExpiracao = dataAtual + timedelta(days=3)
        tokenPartida = ""
        estadoPartidaFinalizada = self.tabelasDominioDB.GetEstadoPartida([Mensagens.EP_CANCELADO, Mensagens.EP_CONCLUIDO, Mensagens.EP_RECUSADO])
        idEstadoPartida = None
        conn = psycopg2.connect(self.connectionString)
        cur = conn.cursor()
        try:
            cur.execute(f"SELECT id from usuario where discord_id_user = '{IdDiscordDesafiante}' and ativo = '1'")
            jogadores.append(cur.fetchone())
            cur.execute(f"SELECT id from usuario where discord_id_user = '{IdDiscordDesafiado}'  and ativo = '1'")
            jogadores.append(cur.fetchone())
            if(jogadores[0] != None and jogadores[1] != None):
                cur.execute(f"""
                    SELECT ID FROM historico_partidas 
                    where (id_usuario_desafiante = '{jogadores[0][0]}' or
                    (id_usuario_desafiante = '{jogadores[1][0]}' and id_usuario_desafiado = '{jogadores[0][0]}')) and
                    (id_estado_partida != {estadoPartidaFinalizada[0].Id} and id_estado_partida != {estadoPartidaFinalizada[1].Id} and id_estado_partida != {estadoPartidaFinalizada[2].Id})
                    """)
                desafianteJaPossuiPartida = cur.fetchone()
                if(desafianteJaPossuiPartida != None):
                    cur.close()
                    conn.close()
                    Retorno.resultado += "O desafiante possui um desafio declarado para ser concluído ou possui partida pendente com quem tentou desafiar."
                    Retorno.corResultado = Cores.Alerta
                    return Retorno
                cur.execute(f"""
                    SELECT ID FROM historico_partidas 
                    where (id_usuario_desafiado = '{jogadores[1][0]}' or
                    (id_usuario_desafiante = '{jogadores[0][0]}' and id_usuario_desafiado = '{jogadores[1][0]}')) and
                    (id_estado_partida != {estadoPartidaFinalizada[0].Id} and id_estado_partida != {estadoPartidaFinalizada[1].Id} and id_estado_partida != {estadoPartidaFinalizada[2].Id})
                    """)

                desafiadoJaPossuiPartida = cur.fetchone()
                if(desafiadoJaPossuiPartida != None):
                    cur.close()
                    conn.close()
                    Retorno.resultado += "O desafiado já possui partida para ser concluída!"
                    Retorno.corResultado = Cores.Alerta
                    return Retorno
                pesquisaToken = ""
                while(pesquisaToken != None):
                    tokenPartida = Gerador.GerarToken()
                    cur.execute(f"SELECT id, token from historico_partidas where token = '{tokenPartida}'")
                    pesquisaToken = cur.fetchone()

                cur.execute(f"SELECT id from estado_partida where nome = '{Mensagens.EP_AGUARDANDO}'")
                idEstadoPartida = cur.fetchone()[0]
                cur.execute(f"""
                    INSERT INTO historico_partidas(
                        id_usuario_requisicao, id_usuario_desafiante, id_usuario_desafiado, id_estado_partida, data_criacao, data_expiracao, token
                        )
                    VALUES(
                        {jogadores[0][0]}, {jogadores[0][0]}, {jogadores[1][0]}, {idEstadoPartida}, '{dataAtual}', '{dataExpiracao}' , '{tokenPartida}'
                    );
                """)
                Retorno.resultado = f"""
                    ## <@{IdDiscordDesafiante}> VS <@{IdDiscordDesafiado}> 
                    ### DESAFIO REGISTRADO PARA ATÉ {dataExpiracao.day}/{dataExpiracao.month}/{dataExpiracao.year}
                    ### TOKEN IDENTIFICADOR DA PARTIDA: 
                    ### ```{tokenPartida}``` """
                Retorno.corResultado = Cores.Sucesso
                
            elif(jogadores[0] == None):
                Retorno.resultado = "O desafiante não está registrado no evento ou está inativo."
                Retorno.corResultado = Cores.Alerta
            elif(jogadores[1] == None):
                Retorno.resultado = "O desafiado não está registrado no evento ou está inativo."
                Retorno.corResultado = Cores.Alerta

            conn.commit()
            cur.close()
            conn.close()

        except Exception as e:
            cur.close()
            conn.close()
            Retorno.resultado += "Ocorreu um erro: \n" + str(e)
            Retorno.corResultado = Cores.Erro
        return Retorno
    
    def RelatarResultado(self, token, vitoriasDesafiante, vitoriasDesafiado):
        Retorno = DBResultado()
        jogadores = []
        dataAtual = datetime.now()
        estadoPartidaFinalizada = self.tabelasDominioDB.GetEstadoPartida([Mensagens.EP_CANCELADO, Mensagens.EP_CONCLUIDO, Mensagens.EP_RECUSADO])
        conn = psycopg2.connect(self.connectionString)
        cur = conn.cursor()
        try:
            cur.close()
            conn.close()
            Retorno.corResultado = Cores.Sucesso
        except Exception as e:
            cur.close()
            conn.close()
            Retorno.resultado += "Ocorreu um erro: \n" + str(e)
            Retorno.corResultado = Cores.Erro
        return Retorno