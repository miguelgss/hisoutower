import psycopg2
import traceback
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
        temporadaAtual = self.tabelasDominioDB.GetTemporadaAtual().Id

        contador = 0
        try:
            cur.execute(f"""
                SELECT id_usuario_desafiante, id_usuario_desafiado, token FROM historico_partidas 
                WHERE data_expiracao < '{dataAtual}' and
                estado_partida = '{Mensagens.EP_AGUARDANDO}' and
                id_temporada = {temporadaAtual}
                """)
            partidasEmExpiracao = cur.fetchall()

            for partida in partidasEmExpiracao:
                cur.execute(f"""
                    INSERT INTO registro_atualizacoes_sistema (dados_trafegados, data_criacao, tipo_atualizacao)
                    VALUES ('Desafiante: {partida[0]}; Desafiado: {partida[1]}; Token: {partida[2]}; DataExpiração: {dataAtual}', '{dataAtual}', '{Mensagens.TA_EXPIRACAO}')
                """)
                contador += 1

            cur.execute(f"""
                    UPDATE historico_partidas set estado_partida = '{Mensagens.EP_EXPIRADO}', data_finalizacao = '{dataAtual}'
                    WHERE data_expiracao < '{dataAtual}' and
                    estado_partida = '{Mensagens.EP_AGUARDANDO}'
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
            Retorno.resultado += "Ocorreu um erro: \n" + str(traceback.format_exc())
            Retorno.corResultado = Cores.Erro
        return Retorno