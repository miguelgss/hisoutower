import psycopg2
import traceback
import math
from datetime import datetime, timedelta
from Utils import Mensagens, Cores, Gerador

from .PostgreSqlConn import PostgreSqlConn
from .DataTransferObjects import DBResultado, FichaDTO
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
        idEstadoPartida = None
        IdDiscordDesafiante = DesafianteUser.id
        IdDiscordDesafiado = DesafiadoUser.id
        temporadaAtual = self.tabelasDominioDB.GetTemporadaAtual().Id

        conn = psycopg2.connect(self.connectionString)
        cur = conn.cursor()
        try:
            stringQueryJogador = f"""
                select usuario.id, ranqueamento.id_temporada, ranqueamento.power from usuario
                join ranqueamento on id_usuario = usuario.id 
                where usuario.discord_id_user  = '$IdDiscord' and usuario.ativo = '1' and ranqueamento.id_temporada = {temporadaAtual}
                order by ranqueamento.id  desc;
            """
            cur.execute(stringQueryJogador.replace('$IdDiscord', str(IdDiscordDesafiante)))
            jogadores.append(cur.fetchone())

            cur.execute(stringQueryJogador.replace('$IdDiscord', str(IdDiscordDesafiado)))
            jogadores.append(cur.fetchone())
            
            if(jogadores[0] != None and jogadores[1] != None):
                if(jogadores[0][0] == jogadores[1][0]):
                    cur.close()
                    conn.close()
                    Retorno.resultado += "Não é possível desafiar a si mesmo."
                    Retorno.corResultado = Cores.Alerta
                    return Retorno
                
                # Valida se o desafiador e/ou desafiante já possuem desafios em andamento
                cur.execute(f"""
                    SELECT ID FROM historico_partidas 
                    where (id_usuario_desafiante = '{jogadores[0][0]}' or
                    (id_usuario_desafiante = '{jogadores[1][0]}' and id_usuario_desafiado = '{jogadores[0][0]}')) and
                    (estado_partida = '{Mensagens.EP_AGUARDANDO}')
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
                    (estado_partida = '{Mensagens.EP_AGUARDANDO}')
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

                cur.execute(f"""
                    INSERT INTO historico_partidas(
                        id_usuario_requisicao, id_usuario_desafiante, id_usuario_desafiado, estado_partida, data_criacao, data_expiracao, token, id_temporada
                        )
                    VALUES(
                        {jogadores[0][0]}, {jogadores[0][0]}, {jogadores[1][0]}, '{Mensagens.EP_AGUARDANDO}', '{dataAtual}', '{dataExpiracao}' , '{tokenPartida}', {temporadaAtual}
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
        idEstadoPartida = None
        conn = psycopg2.connect(self.connectionString)
        cur = conn.cursor()
        try:
            cur.execute(f"""
                select usuario.id, ranqueamento.power from usuario
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
                    (estado_partida = '{Mensagens.EP_AGUARDANDO}')
                """)
            
            partida = cur.fetchone()

            if(partida == None):
                cur.close()
                conn.close()
                Retorno.resultado += "Não há desafios pendentes de conclusão com o token informado ou o desafio com o token especificado não existe."
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
            cur.execute(f"""SELECT power from ranqueamento where id_usuario = {idOponente}""")
            oponente = cur.fetchone()

            if(oponente[0] > jogador[1] or houveDesafioRecente != None): #Comparando os andares de cada jogador
                cur.execute(f"""
                    UPDATE historico_partidas SET
                    data_finalizacao = '{dataAtual}',
                    estado_partida = '{Mensagens.EP_RECUSADO}'
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
            cardDesafiante = await self.ObterPerfil(DiscordDesafiante)
            cardDesafiado = await self.ObterPerfil(DiscordDesafiado)

            stringQueryFicha = f"""
                SELECT u.main
                FROM usuario u
                WHERE u.discord_id_user = '$IdDiscord' 
            """
            cur.execute(stringQueryFicha.replace('$IdDiscord', str(DiscordDesafiante.id)))
            desafianteMain = cur.fetchone()[0]

            cur.execute(stringQueryFicha.replace('$IdDiscord', str(DiscordDesafiado.id)))
            desafiadoMain = cur.fetchone()[0]

            Retorno.arquivo = await Gerador.GerarCardDesafio(cardDesafiante.arquivo, desafianteMain, cardDesafiado.arquivo, desafiadoMain)
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
        estadoPartidasFinalizadas = Mensagens.LISTA_EP_FINALIZADA
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
                select hp.id,id_usuario_desafiante, id_usuario_desafiado, hp.estado_partida
                from historico_partidas hp
                where hp.token like '%{token}'
                """)
            partida = cur.fetchone()
            
            if(partida[3] in estadoPartidasFinalizadas):
                cur.close()
                conn.close()
                Retorno.resultado += f"Essa partida possui o estado de {partida[3]}, não é possível mudar o seu resultado." if partida[3] != Mensagens.EP_EXPIRADO else f"Essa partida foi cancelada por expiração. Um organizador deve relatar seu resultado pelo comando de ConcluirPartidaExpirada."
                Retorno.corResultado = Cores.Alerta
                return Retorno

            VitoriosoId = partida[1] if vitoriasDesafiante > vitoriasDesafiado else partida[2]
            DerrotadoId = partida[1] if vitoriasDesafiante < vitoriasDesafiado else partida[2]
            
            VitoriosoVitorias = vitoriasDesafiante if vitoriasDesafiante > vitoriasDesafiado else vitoriasDesafiado
            DerrotadoVitorias = vitorioasDesafiante if vitoriasDesafiante < vitoriasDesafiado else vitoriasDesafiado

            cur.execute(f"""
                    UPDATE 
                        historico_partidas set estado_partida = '{Mensagens.EP_CONCLUIDO}', 
                        usuario_desafiante_vitorias = {vitoriasDesafiante}, 
                        usuario_desafiado_vitorias = {vitoriasDesafiado}, 
                        id_usuario_vencedor = {VitoriosoId},
                        data_finalizacao = '{dataAtual}'
                    WHERE token like '%{token}'
                """)
            
            resultado = self.AtualizarRanqueamento(VitoriosoId, DerrotadoId, VitoriosoVitorias, DerrotadoVitorias, False)
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

    def AtualizarRanqueamento(self, IdDiscordVitorioso, IdDiscordDerrotado, VitoriosoVitorias, DerrotadoVitorias, foiEmpate):
        Retorno = DBResultado()
        dataAtual = datetime.now()
        tokenPartida = ""
        temporadaAtual = self.tabelasDominioDB.GetTemporadaAtual()
        numeroDeAndaresAtual = self.tabelasDominioDB.GetNumeroDeAndaresAtual()
        andaresAtual = self.tabelasDominioDB.GetAndaresAtual()
        conn = psycopg2.connect(self.connectionString)
        cur = conn.cursor()
        try:
            stringQueryJogador = f"""
                select usuario.id, r.power, r.id, usuario.pontos
                from usuario
                join ranqueamento r on id_usuario = usuario.id
                where usuario.id  = '$IdJogador' and usuario.ativo = '1' and r.id_temporada = {temporadaAtual.Id}
                order by r.id  desc 
                """
            cur.execute(stringQueryJogador.replace('$IdJogador', str(IdDiscordVitorioso)))
            vitorioso = cur.fetchone()

            cur.execute(stringQueryJogador.replace('$IdJogador', str(IdDiscordDerrotado)))
            derrotado = cur.fetchone()
            
            if(foiEmpate):
                Retorno.resultado = "Tudo certo com a atualização de resultados!"
                Retorno.corResultado = Cores.Sucesso
            elif(vitorioso != None and derrotado != None):
                cur.execute(f'select multiplicador from andar where min_points <= {vitorioso[1]} order by min_points desc limit 1;')
                vitoriosoAndarMulti = cur.fetchone()[0]

                cur.execute(f'select multiplicador from andar where min_points <= {derrotado[1]} order by min_points desc limit 1;')
                derrotadoAndarMulti = cur.fetchone()[0]

                vitoriosoGanhoPower = math.ceil((derrotadoAndarMulti - vitoriosoAndarMulti + 1) * 60 + (10 * VitoriosoVitorias - DerrotadoVitorias))
                derrotadoPerdaPower = math.floor((derrotadoAndarMulti - vitoriosoAndarMulti + 1) * 60 + (10 * VitoriosoVitorias - DerrotadoVitorias))

                derrotadoPerdaPower = derrotadoPerdaPower if (derrotado[1] - derrotadoPerdaPower > 0) else 0

                vitoriosoGanhoPontos = (VitoriosoVitorias - DerrotadoVitorias) * 100
                derrotadoGanhoPontos = 100
                cur.execute(
                    f'''
                    update ranqueamento set power = {vitorioso[1] + vitoriosoGanhoPower} where id = {vitorioso[2]};
                    update ranqueamento set power = {derrotado[1] - derrotadoPerdaPower} where id = {derrotado[2]};

                    update usuario set pontos = {vitorioso[3] + vitoriosoGanhoPontos} where id = {vitorioso[0]};
                    update usuario set pontos = {derrotado[3] + derrotadoGanhoPontos} where id = {derrotado[0]};
                    '''
                )
                
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
                select hp.id,id_usuario_desafiante, id_usuario_desafiado, estado_partida
                from historico_partidas hp
                where hp.token = '{token}' and estado_partida = {Mensagens.EP_EXPIRADO}
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
            
            VitoriosoVitorias = vitoriasDesafiante if vitoriasDesafiante > vitoriasDesafiado else vitoriasDesafiado
            DerrotadoVitorias = vitorioasDesafiante if vitoriasDesafiante < vitoriasDesafiado else vitoriasDesafiado
            if(Empate):
                cur.execute(f"""
                        UPDATE 
                            historico_partidas set estado_partida = {Mensagens.EP_EMPATE}, 
                            usuario_desafiante_vitorias = {vitoriasDesafiante}, 
                            usuario_desafiado_vitorias = {vitoriasDesafiado}, 
                            data_finalizacao = '{dataAtual}'
                        WHERE token = '{token}'
                    """)
            else:
                cur.execute(f"""
                        UPDATE 
                            historico_partidas set estado_partida = {Mensagens.EP_JOGADOR_AUSENTE}, 
                            usuario_desafiante_vitorias = {vitoriasDesafiante}, 
                            usuario_desafiado_vitorias = {vitoriasDesafiado}, 
                            id_usuario_vencedor = {VitoriosoId},
                            data_finalizacao = '{dataAtual}'
                        WHERE token = '{token}'
                    """)
            
            resultado = self.AtualizarRanqueamento(VitoriosoId, DerrotadoId, VitoriosoVitorias, DerrotadoVitorias, Empate)
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
