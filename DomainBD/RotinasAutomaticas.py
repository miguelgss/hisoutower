import psycopg2
from datetime import datetime, timedelta
from Utils import Mensagens, Cores, Gerador

from .PostgreSqlConn import PostgreSqlConn
from .TabelasDominioSql import TabelasDominioSql
from .DataTransferObjects import DBResultado

class RotinasAutomaticas(PostgreSqlConn):
    def __init__(self):
        super(RotinasAutomaticas, self).__init__()
        self.tabelasDominioDB = TabelasDominioSql()

    def ExpirarPartidas(self):
        Retorno = DBResultado()
        dataAtual = datetime.now()
        search = None
        conn = psycopg2.connect(self.connectionString)
        cur = conn.cursor()
        tipoAtualizacaoExpiracao = self.tabelasDominioDB.GetTipoAtualizacao([Mensagens.TA_EXPIRACAO])[0]
        estadoPartidaFinalizada = self.tabelasDominioDB.GetEstadoPartida([Mensagens.EP_CANCELADO, Mensagens.EP_CONCLUIDO, Mensagens.EP_RECUSADO])
        contador = 0
        try:
            cur.execute(f"""SELECT id_usuario_desafiante, id_usuario_desafiado, token FROM historico_partidas 
                WHERE data_expiracao < '{dataAtual}' and
                id_estado_partida != {estadoPartidaFinalizada[0].Id} and id_estado_partida != {estadoPartidaFinalizada[1].Id} and id_estado_partida != {estadoPartidaFinalizada[2].Id}
                """)
            partidasEmExpiracao = cur.fetchall()

            for partida in partidasEmExpiracao:
                cur.execute(f"""
                    INSERT INTO registro_atualizacoes_sistema (id_tipo_atualizacao, dados_trafegados, data_criacao)
                    VALUES ({tipoAtualizacaoExpiracao.Id}, 'Desafiante: {partida[0]}; Desafiado: {partida[1]}; Token: {partida[2]}; DataExpiração: {dataAtual}', '{dataAtual}')
                """)
                contador += 1

            cur.execute(f"""
                    UPDATE historico_partidas set id_estado_partida = {estadoPartidaFinalizada[0].Id}, data_finalizacao = '{dataAtual}'
                    WHERE data_expiracao < '{dataAtual}' and
                    id_estado_partida != {estadoPartidaFinalizada[0].Id} and id_estado_partida != {estadoPartidaFinalizada[1].Id} and id_estado_partida != {estadoPartidaFinalizada[2].Id}
                """)
                
            Retorno.resultado = f"Número de partidas canceladas por expiração desde a última atualização: {contador}"

            conn.commit()
            cur.close()
            conn.close()
            Retorno.corResultado = Cores.Sucesso
        except Exception as e:
            conn.rollback()
            cur.close()
            conn.close()
            Retorno.resultado += "Ocorreu um erro: \n" + str(e)
            Retorno.corResultado = Cores.Erro
        return Retorno