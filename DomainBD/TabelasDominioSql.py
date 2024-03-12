import psycopg2
from datetime import datetime, timedelta
from Utils import Mensagens, Cores, Gerador

from .PostgreSqlConn import PostgreSqlConn
from .DataTransferObjects import TipoAtualizacaoDTO, EstadoPartidaDTO

class TabelasDominioSql(PostgreSqlConn):
    def __init__(self):
        super(TabelasDominioSql, self).__init__()

    def GetEstadoPartida(self, filtro):
        Retorno = []
        estadosPartida = ""
        conn = psycopg2.connect(self.connectionString)
        cur = conn.cursor()
        stringQuery = "SELECT id, nome FROM estado_partida "
        if(filtro and filtro != ''):
            stringQuery += f"WHERE nome = '{filtro[0]}' "
            for nome in filtro[1:]:
                stringQuery += f"OR nome = '{nome}'"
            stringQuery += ";"
        cur.execute(stringQuery)
        estadosPartida = cur.fetchall()

        for estado in estadosPartida:
            estadoUnidade = EstadoPartidaDTO()
            estadoUnidade.Id = estado[0]
            estadoUnidade.Nome = estado[1]
            Retorno.append(estadoUnidade)
            
        cur.close()
        conn.close()

        return Retorno

    def GetTipoAtualizacao(self, filtro):
        Retorno = []
        tiposAtualizacao = ""
        conn = psycopg2.connect(self.connectionString)
        cur = conn.cursor()
        stringQuery = "SELECT id, nome FROM tipo_atualizacao "
        if(filtro and filtro != ''):
            stringQuery += f"WHERE nome = '{filtro[0]}' "
            for nome in filtro[1:]:
                stringQuery += f"OR nome = '{nome}'"
            stringQuery += ";"
        cur.execute(stringQuery)
        tiposAtualizacao = cur.fetchall()

        for atualizacao in tiposAtualizacao:
            tipoAt = TipoAtualizacaoDTO()
            tipoAt.Id = atualizacao[0]
            tipoAt.Nome = atualizacao[1]
            Retorno.append(tipoAt)
        
        cur.close()
        conn.close()

        return Retorno