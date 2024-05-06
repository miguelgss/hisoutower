import psycopg2
import traceback
from datetime import datetime, timedelta
from Utils import Mensagens, Cores, Gerador

from .PostgreSqlConn import PostgreSqlConn
from .DataTransferObjects import DBResultado
from .TabelasDominioSql import TabelasDominioSql

class DesafioSql(PostgreSqlConn):
    def __init__(self):
        super(DesafioSql, self).__init__()
        self.tabelasDominioDB = TabelasDominioSql()

    async def Desafiar(self, DesafianteUser, DesafiadoUser):
        Retorno = DBResultado()
        jogadores = []
        jogadoresTop = []
        dataAtual = datetime.now()
        dataExpiracao = dataAtual + timedelta(days=3)
        tokenPartida = ""
        estadoPartidaAguardando = self.tabelasDominioDB.GetEstadoPartida([Mensagens.EP_AGUARDANDO])
        idEstadoPartida = None
        IdDiscordDesafiante = DesafianteUser.id
        IdDiscordDesafiado = DesafiadoUser.id
        conn = psycopg2.connect(self.connectionString)
        cur = conn.cursor()
        try:
            cur.execute(f"""
                select usuario.id, ranqueamento.id_temporada, ranqueamento.id_andar_atual, ranqueamento.vitorias_consecutivas from usuario
                join ranqueamento on id_usuario = usuario.id 
                where usuario.discord_id_user  = '{IdDiscordDesafiante}' and usuario.ativo = '1'
                order by ranqueamento.id  desc 
                """)
            jogadores.append(cur.fetchone())
            cur.execute(f"""
                select usuario.id, ranqueamento.id_temporada, ranqueamento.id_andar_atual, ranqueamento.vitorias_consecutivas from usuario
                join ranqueamento on id_usuario = usuario.id 
                where usuario.discord_id_user  = '{IdDiscordDesafiado}' and usuario.ativo = '1'
                order by ranqueamento.id  desc 
                """)
            jogadores.append(cur.fetchone())

            cur.execute(f"""
                select usuario.id, ranqueamento.id_andar_atual, ranqueamento.partidas_para_subir, ranqueamento.partidas_para_descer, ranqueamento.vitorias_consecutivas
                from usuario
                join ranqueamento on id_usuario = usuario.id 
                where usuario.ativo = '1' and ranqueamento.id_andar_atual < 6
                order by ranqueamento.id_andar_atual 
                """)
            jogadoresTop = cur.fetchall()
            
            if(jogadores[0] != None and jogadores[1] != None):
                if(jogadores[0][0] == jogadores[1][0]):
                    cur.close()
                    conn.close()
                    Retorno.resultado += "Não é possível desafiar a si mesmo."
                    Retorno.corResultado = Cores.Alerta
                    return Retorno

                # Comparação de andares entre os jogadores:
                if(jogadores[0][2] > 2 and len(jogadoresTop) > 1):
                    if(jogadores[1][2] == 1):
                        cur.close()
                        conn.close()
                        Retorno.resultado += "Apenas o jogador mais próximo do campeão pode desafiá-lo."
                        Retorno.corResultado = Cores.Alerta
                        return Retorno
                
                minimoVitorias = 2
                if  (
                        (jogadores[0][2] > 6 and jogadoresTop != [] and jogadores[1][2] <= jogadoresTop[-1][1]) or 
                        (jogadores[0][2] == 6 and jogadoresTop != [] and (jogadores[1][2] < jogadoresTop[-1][1]) or 
                        (jogadores[0][3] < minimoVitorias and jogadoresTop != [] and jogadores[1][2] == jogadoresTop[-1][1]))
                    ):
                    cur.close()
                    conn.close()
                    Retorno.resultado += "É necessário estar no maior andar possível e **possuir duas vitórias consecutivas** para desafiar o último da elite. **Jogadores em andar da torre não podem desafiar jogadores celestiais, exceto pelo último jogador celestial.**"
                    Retorno.corResultado = Cores.Alerta
                    return Retorno

                # Valida se o desafiador e/ou desafiante já possuem desafios em andamento
                cur.execute(f"""
                    SELECT ID FROM historico_partidas 
                    where (id_usuario_desafiante = '{jogadores[0][0]}' or
                    (id_usuario_desafiante = '{jogadores[1][0]}' and id_usuario_desafiado = '{jogadores[0][0]}')) and
                    (id_estado_partida = {estadoPartidaAguardando[0].Id})
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
                    (id_estado_partida = {estadoPartidaAguardando[0].Id})
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

                imgDesafio = await self.GerarImagemDesafio(DesafianteUser, DesafiadoUser)
                Retorno.arquivo = imgDesafio.arquivo
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
            Retorno.resultado += "Ocorreu um erro: \n" + str(traceback.format_exc())
            Retorno.corResultado = Cores.Erro
        return Retorno
    
    def RecusarDesafio(self, token, IdDiscordAnulador):
        Retorno = DBResultado()
        dataAtual = datetime.now()
        estadoPartidaFinalizada = self.tabelasDominioDB.GetEstadoPartida(Mensagens.LISTA_EP_FINALIZADA)
        estadoPartidaAguardando = self.tabelasDominioDB.GetEstadoPartida([Mensagens.EP_AGUARDANDO])
        idEstadoPartida = None
        conn = psycopg2.connect(self.connectionString)
        cur = conn.cursor()
        try:
            cur.execute(f"""
                select usuario.id, ranqueamento.id_andar_atual from usuario
                join ranqueamento on ranqueamento.id_usuario = usuario.id
                where usuario.discord_id_user  = '{IdDiscordAnulador}' and usuario.ativo = '1'
                """)
            jogador = cur.fetchone()
            
            if(jogador == None):
                cur.close()
                conn.close()
                Retorno.resultado += "O usuário não existe."
                Retorno.corResultado = Cores.Erro
                return Retorno

            cur.execute(f"""
                    SELECT ID, id_usuario_desafiante, id_usuario_desafiado FROM historico_partidas 
                    where token = '{token}' and 
                    (id_usuario_desafiado = {jogador[0]} or
                    id_usuario_desafiante = {jogador[0]} ) and
                    (id_estado_partida = {estadoPartidaAguardando[0].Id})
                """)
            
            partida = cur.fetchone()

            if(partida == None):
                cur.close()
                conn.close()
                Retorno.resultado += "Não há desafios pendentes de conclusão ou o desafio com o token especificado não existe."
                Retorno.corResultado = Cores.Erro
                return Retorno
            
            cur.execute(f"""
                    SELECT ID, id_usuario_desafiado, id_usuario_desafiante FROM historico_partidas 
                    WHERE 
                    data_criacao + '3 day'::interval < '{dataAtual}' and
                    (id_usuario_desafiado = {jogador[0]} or
                    id_usuario_desafiante = {jogador[0]})
                """)
            
            houveDesafioRecente = cur.fetchone()

            idOponente = partida[1] if partida[1] == jogador[0] else partida[2]
            cur.execute(f"""SELECT id_andar_atual from ranqueamento where id_usuario = {idOponente}""")
            oponente = cur.fetchone()

            if(oponente[0] > jogador[1] or houveDesafioRecente != None): #Comparando os andares de cada jogador
                cur.execute(f"""
                    UPDATE historico_partidas SET
                    data_finalizacao = '{dataAtual}',
                    id_estado_partida = {estadoPartidaFinalizada[0].Id}
                    WHERE token = '{token}'
                """)

                Retorno.resultado = f"""
                    ## Desafio de token {token} foi recusado.
                    """
                Retorno.corResultado = Cores.Sucesso
            else:
                Retorno.resultado = f"""
                    ## É necessário que o oponente seja de um andar maior para recusar seu desafio ou que você já tenha sido desafiado pelo desafiante dessa partida dentro de 72 horas.
                    """
                Retorno.corResultado = Cores.Alerta
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            cur.close()
            conn.close()
            Retorno.resultado += "Ocorreu um erro: \n" + str(traceback.format_exc())
            Retorno.corResultado = Cores.Erro

        return Retorno

    async def GerarImagemDesafio(self, DiscordDesafiante, DiscordDesafiado):
        Retorno = DBResultado()        
        conn = psycopg2.connect(self.connectionString)
        cur = conn.cursor()
        try:
            cardDesafiante = await self.ObterPerfil(DiscordDesafiante, '')
            cardDesafiado = await self.ObterPerfil(DiscordDesafiado, '')
            cur.execute(f"""
                        SELECT usuario.tipo_ficha
                        FROM usuario
                        WHERE usuario.discord_id_user = '{DiscordDesafiante.id}' 
                        """)
            desafianteChar = cur.fetchone()[0]
            cur.execute(f"""
                        SELECT usuario.tipo_ficha
                        FROM usuario
                        WHERE usuario.discord_id_user = '{DiscordDesafiado.id}' 
                        """)
            desafiadoChar = cur.fetchone()[0]
            Retorno.arquivo = await Gerador.GerarCardDesafio(cardDesafiante.arquivo, desafianteChar, cardDesafiado.arquivo, desafiadoChar)
            Retorno.corResultado = Cores.Sucesso
        except Exception as e:
            cur.close()
            conn.close()
            Retorno.resultado += "Ocorreu um erro: \n" + str(traceback.format_exc())
            Retorno.corResultado = Cores.Erro

        return Retorno

    def RelatarResultado(self, token, vitoriasDesafiante, vitoriasDesafiado):
        Retorno = DBResultado()
        partida = ''
        dataAtual = datetime.now()
        estadoPartidaFinalizada = self.tabelasDominioDB.GetEstadoPartida(Mensagens.LISTA_EP_FINALIZADA)
        estadoPartidaConcluida = self.tabelasDominioDB.GetEstadoPartida([Mensagens.EP_CONCLUIDO])
        idEstadoPartidasFinalizadas = [o.Id for o in estadoPartidaFinalizada]
        VitoriosoId = 0
        conn = psycopg2.connect(self.connectionString)
        cur = conn.cursor()
        try:
            if(vitoriasDesafiante != Mensagens.FT_NUMERO and 
            vitoriasDesafiado != Mensagens.FT_NUMERO or 
            (vitoriasDesafiante > Mensagens.FT_NUMERO or vitoriasDesafiado > Mensagens.FT_NUMERO) or 
            (vitoriasDesafiante == Mensagens.FT_NUMERO and vitoriasDesafiado == Mensagens.FT_NUMERO)):
                cur.close()
                conn.close()
                Retorno.resultado += f"As partidas são FT{Mensagens.FT_NUMERO}! Apenas um deve deve ter {Mensagens.FT_NUMERO} vitórias para considerar a partida finalizada. Favor reavaliar os números passados."
                Retorno.corResultado = Cores.Alerta
                return Retorno
            cur.execute(f"""     
                select hp.id,id_usuario_desafiante, id_usuario_desafiado, id_estado_partida, ep.nome
                from historico_partidas hp
                join estado_partida ep on ep.id = hp.id_estado_partida
                where hp.token = '{token}'
                """)
            partida = cur.fetchone()
            
            if(partida[3] in idEstadoPartidasFinalizadas):
                cur.close()
                conn.close()
                Retorno.resultado += f"Essa partida possui o estado de {partida[4]}, não é possível mudar o seu resultado." if partida[3] != Mensagens.EP_CANCELADO else f"Essa partida foi cancelada por expiração. Favor relatar seu resultado pelo comando de ConcluirPartidaExpirada."
                Retorno.corResultado = Cores.Alerta
                return Retorno

            VitoriosoId = partida[1] if vitoriasDesafiante > vitoriasDesafiado else partida[2]
            DerrotadoId = partida[1] if vitoriasDesafiante < vitoriasDesafiado else partida[2]
            
            cur.execute(f"""
                    UPDATE 
                        historico_partidas set id_estado_partida = {estadoPartidaConcluida[0].Id}, 
                        usuario_desafiante_vitorias = {vitoriasDesafiante}, 
                        usuario_desafiado_vitorias = {vitoriasDesafiado}, 
                        id_usuario_vencedor = {VitoriosoId},
                        data_finalizacao = '{dataAtual}'
                    WHERE token = '{token}'
                """)
            
            resultado = self.AtualizarRanqueamento(VitoriosoId, DerrotadoId, False)
            if(resultado.resultado != "Tudo certo com a atualização de resultados!"): 
                cur.close()
                conn.close()
                Retorno.resultado += resultado.resultado
                Retorno.corResultado = Cores.Alerta
                return Retorno
            
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
            Retorno.resultado += "Ocorreu um erro: \n" + str(traceback.format_exc())
            Retorno.corResultado = Cores.Erro
        return Retorno

    def AtualizarRanqueamento(self, IdDiscordVitorioso, IdDiscordDerrotado, foiEmpate):
        Retorno = DBResultado()
        dataAtual = datetime.now()
        jogadores = []
        jogadoresTop = []
        tokenPartida = ""
        temporadaAtual = self.tabelasDominioDB.GetTemporadaAtual()
        numeroDeAndaresAtual = self.tabelasDominioDB.GetNumeroDeAndaresAtual()
        conn = psycopg2.connect(self.connectionString)
        cur = conn.cursor()
        try:
            cur.execute(f"""
                select usuario.id, ranqueamento.id_andar_atual, ranqueamento.partidas_para_subir, ranqueamento.partidas_para_descer, ranqueamento.vitorias_consecutivas
                from usuario
                join ranqueamento on id_usuario = usuario.id 
                where usuario.id  = {IdDiscordVitorioso} and usuario.ativo = '1' and ranqueamento.id_temporada = {temporadaAtual.Id}
                order by ranqueamento.id  desc 
                """)
            jogadores.append(cur.fetchone())

            cur.execute(f"""
                select usuario.id, ranqueamento.id_andar_atual, ranqueamento.partidas_para_subir, ranqueamento.partidas_para_descer, ranqueamento.vitorias_consecutivas
                from usuario
                join ranqueamento on id_usuario = usuario.id 
                where usuario.id  = {IdDiscordDerrotado} and usuario.ativo = '1' and ranqueamento.id_temporada = {temporadaAtual.Id}
                order by ranqueamento.id  desc 
                """)
            jogadores.append(cur.fetchone())

            cur.execute(f"""
                select usuario.id, ranqueamento.id_andar_atual, ranqueamento.partidas_para_subir, ranqueamento.partidas_para_descer, ranqueamento.vitorias_consecutivas
                from usuario
                join ranqueamento on id_usuario = usuario.id 
                where usuario.ativo = '1' and ranqueamento.id_andar_atual < 6 and ranqueamento.id_temporada = {temporadaAtual.Id}
                order by ranqueamento.id_andar_atual
                """)
            jogadoresTop = cur.fetchall()
            
            if(foiEmpate):
                Retorno.resultado = "Tudo certo com a atualização de resultados!"
                Retorno.corResultado = Cores.Sucesso
            elif(jogadores[0] != None and jogadores[1] != None):
                if(jogadores[0][1] > 5): # Se o andar do jogador vitorioso for da torre...
                    if(jogadores[1][1] > 5): # Se o derrotado for da torre...
                        # Atualizando dados do vencedor
                        novoAndar = jogadores[0][1]
                        partidasParaSubir = 2
                        partidasParaDescer = jogadores[0][3]
                        if(jogadores[0][1] <= jogadores[1][1]):
                            partidasParaDescer = 2
                        if(jogadores[0][1] == 6 and len(jogadoresTop) < 1 and jogadores[0][4] > 1):
                            novoAndar = 1
                        elif(jogadores[0][2] < 2):
                            novoAndar = jogadores[0][1] - 1 if jogadores[0][1] > 6 else jogadores[0][1]
                        else:
                            partidasParaSubir = 1
                        cur.execute(f"""
                            UPDATE ranqueamento SET
                                id_andar_atual = {novoAndar},
                                partidas_para_subir = {partidasParaSubir},
                                partidas_para_descer = {partidasParaDescer},
                                data_atualizacao = '{dataAtual}',
                                vitorias_consecutivas = {(jogadores[0][4] + 1)}
                                WHERE id_usuario = {jogadores[0][0]} and id_temporada = {temporadaAtual.Id};
                            """)

                        # Atualizando dados do derrotado
                        if(jogadores[1][3] < 2):
                            estaNoUltimoAndar = 0 if jogadores[1][1] == numeroDeAndaresAtual else 1
                            cur.execute(f"""
                                UPDATE ranqueamento SET
                                    id_andar_atual = {(jogadores[1][1] + estaNoUltimoAndar)},
                                    partidas_para_subir = 2,
                                    partidas_para_descer = 2,
                                    data_atualizacao = '{dataAtual}',
                                    vitorias_consecutivas = 0
                                    WHERE id_usuario = {jogadores[1][0]} and id_temporada = {temporadaAtual.Id};
                                """)
                        else:
                            estaNoUltimoAndar = 2 if jogadores[1][1] == numeroDeAndaresAtual else 1
                            cur.execute(f"""
                                UPDATE ranqueamento SET
                                    partidas_para_subir = 2,
                                    partidas_para_descer = {estaNoUltimoAndar},
                                    data_atualizacao = '{dataAtual}',
                                    vitorias_consecutivas = 0
                                    WHERE id_usuario = {jogadores[1][0]} and id_temporada = {temporadaAtual.Id};
                                """)

                    # Se o derrotado for da elite...
                    elif(jogadores[0][1] == 6 and jogadoresTop != None and jogadores[1][1] == jogadoresTop[-1][1]):
                        cur.execute(f"""
                            UPDATE ranqueamento SET
                                id_andar_atual = {jogadores[-1][1]},
                                partidas_para_subir = 2,
                                partidas_para_descer = 2,
                                data_atualizacao = '{dataAtual}',
                                vitorias_consecutivas = {(jogadores[0][4] + 1)}
                                WHERE id_usuario = {jogadores[0][0]} and id_temporada = {temporadaAtual.Id};
                            """)
                        cur.execute(f"""
                            UPDATE ranqueamento SET
                                id_andar_atual = {(jogadores[1][1] + 1)},
                                partidas_para_subir = 2,
                                partidas_para_descer = 2,
                                data_atualizacao = '{dataAtual}',
                                vitorias_consecutivas = 0
                                WHERE id_usuario = {jogadores[1][0]} and id_temporada = {temporadaAtual.Id};
                            """)
                        
                else: # Se o jogador vitorioso fizer parte dos celestiais...
                    if(jogadores[0][1] >= jogadores[1][1]): # Comparando os andares
                        posicaoTomada = jogadores[0][1] - 1

                        cur.execute(f"""
                            UPDATE ranqueamento SET
                                id_andar_atual = {posicaoTomada},
                                partidas_para_subir = 2,
                                partidas_para_descer = 2,
                                data_atualizacao = '{dataAtual}',
                                vitorias_consecutivas = {(jogadores[0][4] + 1)}
                                WHERE id_usuario = {jogadores[0][0]} and id_temporada = {temporadaAtual.Id};
                            """)

                        vaiTomarPosicaoDoPerdedor = 1 if posicaoTomada == jogadores[1][1] else 0
                        cur.execute(f"""
                            UPDATE ranqueamento SET
                                id_andar_atual = {jogadores[1][1] + vaiTomarPosicaoDoPerdedor},
                                partidas_para_subir = 2,
                                partidas_para_descer = 2,
                                data_atualizacao = '{dataAtual}',
                                vitorias_consecutivas = 0
                                WHERE id_usuario = {jogadores[1][0]} and id_temporada = {temporadaAtual.Id};
                            """) 
                    else:
                        cur.execute(f"""
                            UPDATE ranqueamento SET
                                data_atualizacao = '{dataAtual}',
                                vitorias_consecutivas = {(jogadores[0][4] + 1)}
                                WHERE id_usuario = {jogadores[0][0]} and id_temporada = {temporadaAtual.Id};
                            """)
                
                Retorno.resultado = "Tudo certo com a atualização de resultados!"
                Retorno.corResultado = Cores.Sucesso

            conn.commit()
            cur.close()
            conn.close()

            
        except Exception as e:
            conn.rollback()
            cur.close()
            conn.close()
            Retorno.resultado += "Ocorreu um erro: \n" + str(traceback.format_exc())
            Retorno.corResultado = Cores.Erro
        return Retorno
    
    def ConcluirPartidaExpirada(self, token, vitoriasDesafiante, vitoriasDesafiado):
        Retorno = DBResultado()
        partida = ''
        dataAtual = datetime.now()
        estadoPartidaCancelada = self.tabelasDominioDB.GetEstadoPartida([Mensagens.EP_CANCELADO])
        estadoPartidaEmpate = self.tabelasDominioDB.GetEstadoPartida([Mensagens.EP_EMPATE])
        estadoPartidaVitoriaAusencia = self.tabelasDominioDB.GetEstadoPartida([Mensagens.EP_JOGADOR_AUSENTE])
        VitoriosoId = 0
        conn = psycopg2.connect(self.connectionString)
        cur = conn.cursor()
        try:
            Empate = vitoriasDesafiante == 0 and vitoriasDesafiado == 0

            if(not Empate and (vitoriasDesafiante != 4 and vitoriasDesafiado != 4 or 
                (vitoriasDesafiante > 4 or vitoriasDesafiado > 4) or 
                (vitoriasDesafiante == 4 and vitoriasDesafiado == 4))):
                cur.close()
                conn.close()
                Retorno.resultado += "As partidas são FT4! Apenas um deve deve ter 4 vitórias para considerar a partida finalizada. Favor reavaliar os números passados."
                Retorno.corResultado = Cores.Alerta
                return Retorno
            cur.execute(f"""     
                select hp.id,id_usuario_desafiante, id_usuario_desafiado, id_estado_partida, ep.nome
                from historico_partidas hp
                join estado_partida ep on ep.id = hp.id_estado_partida
                where hp.token = '{token}' and id_estado_partida = {estadoPartidaCancelada[0].Id}
                """)
            partida = cur.fetchone()

            if(partida == None):
                cur.close()
                conn.close()
                Retorno.resultado += "A partida não foi encontrada."
                Retorno.corResultado = Cores.Alerta
                return Retorno

            VitoriosoId = partida[1] if vitoriasDesafiante > vitoriasDesafiado else partida[2]
            DerrotadoId = partida[1] if vitoriasDesafiante < vitoriasDesafiado else partida[2]
            
            if(Empate):
                cur.execute(f"""
                        UPDATE 
                            historico_partidas set id_estado_partida = {estadoPartidaEmpate[0].Id}, 
                            usuario_desafiante_vitorias = {vitoriasDesafiante}, 
                            usuario_desafiado_vitorias = {vitoriasDesafiado}, 
                            data_finalizacao = '{dataAtual}'
                        WHERE token = '{token}'
                    """)
            else:
                cur.execute(f"""
                        UPDATE 
                            historico_partidas set id_estado_partida = {estadoPartidaVitoriaAusencia[0].Id}, 
                            usuario_desafiante_vitorias = {vitoriasDesafiante}, 
                            usuario_desafiado_vitorias = {vitoriasDesafiado}, 
                            id_usuario_vencedor = {VitoriosoId},
                            data_finalizacao = '{dataAtual}'
                        WHERE token = '{token}'
                    """)
            
            resultado = self.AtualizarRanqueamento(VitoriosoId, DerrotadoId, Empate)
            if(resultado.resultado != "Tudo certo com a atualização de resultados!"): 
                cur.close()
                conn.close()
                Retorno.resultado += resultado.resultado
                Retorno.corResultado = Cores.Alerta
                return Retorno
            
            usuarios = []
            cur.execute(f"SELECT id, discord_id_user FROM usuario WHERE id = {partida[1]}")
            usuarios.append(cur.fetchone())
            cur.execute(f"SELECT id, discord_id_user FROM usuario WHERE id = {partida[2]}")
            usuarios.append(cur.fetchone())

            vitoriosoNome = usuarios[0][1] if usuarios[0][0] == VitoriosoId else usuarios[1][1]
            ausenteNome = usuarios[0][1] if usuarios[0][0] != VitoriosoId else usuarios[1][1]
            if(Empate):
                Retorno.resultado = f"""
                    ## <@{usuarios[0][1]}> [{vitoriasDesafiante}] VS [{vitoriasDesafiado}] <@{usuarios[1][1]}> 
                    ### PARTIDA CONCLUÍDA COMO EMPATE.
                    """
            else:
                Retorno.resultado = f"""
                    ## <@{usuarios[0][1]}> [{vitoriasDesafiante}] VS [{vitoriasDesafiado}] <@{usuarios[1][1]}> 
                    ### PARTIDA CONCLUÍDA POR CONTA DA AUSÊNCIA DE <@{ausenteNome}>. PARABÉNS <@{vitoriosoNome}>
                    """ 
            
            Retorno.corResultado = Cores.Sucesso
            conn.commit()
            cur.close()
            conn.close()
            Retorno.corResultado = Cores.Sucesso
        except Exception as e:
            cur.close()
            conn.close()
            Retorno.resultado += "Ocorreu um erro: \n" + str(traceback.format_exc())
            Retorno.corResultado = Cores.Erro
        return Retorno
