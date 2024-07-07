import psycopg2
from datetime import datetime, timedelta
from Utils import Mensagens, Cores, Gerador

from .PostgreSqlConn import PostgreSqlConn
from .DataTransferObjects import TipoAtualizacaoDTO, EstadoPartidaDTO, TemporadaDTO, ProdutoDTO, AndarDTO

class TabelasDominioSql(PostgreSqlConn):
    def __init__(self):
        super(TabelasDominioSql, self).__init__()

    def GetTemporadaAtual(self):
        Retorno = TemporadaDTO()
        temporada = None
        conn = psycopg2.connect(self.connectionString)
        cur = conn.cursor()
        stringQuery = "SELECT id, nome, temporada_ativa FROM temporada WHERE temporada_ativa = '1' ORDER BY temporada.id DESC LIMIT 1 "
        cur.execute(stringQuery)
        temporada = cur.fetchone()

        Retorno.Id = temporada[0]
        Retorno.Nome = temporada[1]
        Retorno.TemporadaAtiva = temporada[2]
               
        cur.close()
        conn.close()

        return Retorno

    def GetListaProdutosCorpoGratuitos(self) -> list[ProdutoDTO]:
        Retorno = []
        conn = psycopg2.connect(self.connectionString)
        cur = conn.cursor()
        cur.execute(f"SELECT id, nome, tipo from PRODUTO where tipo = '{Mensagens.TP_CORPO}' and preco = 0")
        produtos = cur.fetchall()

        for produto in produtos:
            novoProd = ProdutoDTO()
            novoProd.Id = produto[0]
            novoProd.Nome = produto[1]
            novoProd.TipoProduto = produto[2]
            Retorno.append(novoProd)

        cur.close()
        conn.close()
        return Retorno

    def GetAndaresAtual(self) -> list[AndarDTO]:
        Retorno = []
        conn = psycopg2.connect(self.connectionString)
        cur = conn.cursor()
        cur.execute(f"SELECT id, nome, min_points, ativo, data_criacao, boss from ANDAR order by min_points DESC")
        andares = cur.fetchall()

        for andar in andares:
            novoAndar = AndarDTO()
            novoAndar.Id = andares[0]
            novoAndar.Nome = andares[1]
            novoAndar.MinimoPoints = andares[2]
            novoAndar.Ativo = andares[3] == '1'
            novoAndar.Boss = andares[5] == '1'
            Retorno.append(novoAndar)

        cur.close()
        conn.close()
        return Retorno

    def GetNumeroDeAndaresAtual(self):
        Retorno = None
        numeroAndares = None
        conn = psycopg2.connect(self.connectionString)
        cur = conn.cursor()
        stringQuery = "SELECT id, nome FROM andar ORDER BY id"
        cur.execute(stringQuery)
        numeroAndares = cur.fetchall()
        
        Retorno = len(numeroAndares)
        cur.close()
        conn.close()

        return Retorno