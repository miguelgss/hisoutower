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
            cur.execute(f"""
                select usuario.id, ranqueamento.id_temporada, ranqueamento.id_andar_atual  from usuario
                join ranqueamento on id_usuario = usuario.id 
                where usuario.discord_id_user  = '{IdDiscordDesafiante}' and usuario.ativo = '1'
                order by ranqueamento.id  desc 
                """)
            jogadores.append(cur.fetchone())
            cur.execute(f"""
                select usuario.id, ranqueamento.id_temporada, ranqueamento.id_andar_atual  from usuario
                join ranqueamento on id_usuario = usuario.id 
                where usuario.discord_id_user  = '{IdDiscordDesafiado}' and usuario.ativo = '1'
                order by ranqueamento.id  desc 
                """)
            jogadores.append(cur.fetchone())

            print(jogadores)
            if(jogadores[0] != None and jogadores[1] != None):

                # Comparação de andares entre os jogadores:
                if(jogadores[0][2] > 2):
                    if(jogadores[1][2] == 1):
                        cur.close()
                        conn.close()
                        Retorno.resultado += "Apenas o jogador mais próximo do campeão pode desafiá-lo."
                        Retorno.corResultado = Cores.Alerta
                        return Retorno

                # Valida se o desafiador e/ou desafiante já possuem desafios em andamento
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
        partida = ''
        dataAtual = datetime.now()
        estadoPartidaFinalizada = self.tabelasDominioDB.GetEstadoPartida([Mensagens.EP_CANCELADO, Mensagens.EP_CONCLUIDO, Mensagens.EP_RECUSADO])
        estadoPartidaConcluida = self.tabelasDominioDB.GetEstadoPartida([Mensagens.EP_CONCLUIDO])
        idEstadoPartidasFinalizadas = [o.Id for o in estadoPartidaFinalizada]
        VitoriosoId = 0
        conn = psycopg2.connect(self.connectionString)
        cur = conn.cursor()
        try:
            if(vitoriasDesafiante != 4 and vitoriasDesafiado != 4 or (vitoriasDesafiante > 4 or vitoriasDesafiado > 4) or (vitoriasDesafiante == 4 and vitoriasDesafiado == 4)):
                cur.close()
                conn.close()
                Retorno.resultado += "As partidas são FT4! Apenas um deve deve ter 4 vitórias para considerar a partida finalizada. Favor reavaliar os números passados."
                Retorno.corResultado = Cores.Alerta
                return Retorno
            cur.execute(f"""     
                select id,id_usuario_desafiante, id_usuario_desafiado, id_estado_partida
                from historico_partidas hp
                where hp.token = '{token}'
                """)
            partida = cur.fetchone()
            
            if(partida[3] in idEstadoPartidasFinalizadas):
                cur.close()
                conn.close()
                Retorno.resultado += "Essa partida já foi concluída ou cancelada, não é possível mudar o seu estado ou resultado."
                Retorno.corResultado = Cores.Alerta
                return Retorno

            VitoriosoId = partida[1] if vitoriasDesafiante > vitoriasDesafiado else partida[2]
            cur.execute(f"""
                    UPDATE 
                        historico_partidas set id_estado_partida = {estadoPartidaConcluida[0].Id}, 
                        usuario_desafiante_vitorias = {vitoriasDesafiante}, 
                        usuario_desafiado_vitorias = {vitoriasDesafiado}, 
                        id_usuario_vencedor = {VitoriosoId},
                        data_finalizacao = '{dataAtual}'
                    WHERE token = '{token}'
                """)
            
            # ADICIONAR MÉTODO GERAL PARA ATUALIZAR O RANQUEAMENTO POR CONTA DA MODIFICAÇÃO DA PARTIDA
            print('chegou aqui')
            usuarios = []
            cur.execute(f"SELECT id, discord_id_user FROM usuario WHERE id = {partida[1]}")
            usuarios.append(cur.fetchone())
            cur.execute(f"SELECT id, discord_id_user FROM usuario WHERE id = {partida[2]}")
            usuarios.append(cur.fetchone())

            vitoriosoNome = usuarios[0][1] if usuarios[0][0] == VitoriosoId else usuarios[1][1]
            
            Retorno.resultado = f"""
                    ## <@{usuarios[0][1]}> [{vitoriasDesafiante}] VS [{vitoriasDesafiado}] <@{usuarios[1][1]}> 
                    ### PARTIDA CONCLUÍDA! PARABÉNS <@{vitoriosoNome}>
                    """

            Retorno.corResultado = Cores.Sucesso
            conn.commit()
            cur.close()
            conn.close()
            Retorno.corResultado = Cores.Sucesso
        except Exception as e:
            cur.close()
            conn.close()
            Retorno.resultado += "Ocorreu um erro: \n" + str(e)
            Retorno.corResultado = Cores.Erro
        return Retorno