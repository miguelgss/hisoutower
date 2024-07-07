import psycopg2
import traceback
from datetime import datetime, timedelta
from table2ascii import table2ascii as t2a, PresetStyle

from .PostgreSqlConn import PostgreSqlConn
from Utils import Mensagens, Cores, Gerador
from .DataTransferObjects import DBResultado, UsuarioDTO
from .TabelasDominioSql import TabelasDominioSql

class UsuarioSql(PostgreSqlConn):
    def __init__(self):
        super(UsuarioSql, self).__init__()
        self.Gerador = Gerador()
        self.tabelasDominioDB = TabelasDominioSql()

    def RegisterUser(self, IdDiscord, Nickname, TipoPerfil):
        Retorno = DBResultado()
        resultado = None
        temporadaAtual = self.tabelasDominioDB.GetTemporadaAtual()
        produtosFichaCorpo = self.tabelasDominioDB.GetListaProdutosCorpoGratuitos()

        idGeradoUsuario = None
        conn = psycopg2.connect(self.connectionString)
        cur = conn.cursor()
        try:
            cur.execute(f"SELECT * FROM usuario WHERE discord_id_user = '{IdDiscord}' AND nome = '{Nickname}';")
            
            pesquisa = cur.fetchone()
            if(pesquisa == None):
                cur.execute(f"""
                    INSERT INTO usuario(discord_id_user, nome, tipo_perfil, ativo, dados_publicos, data_criacao)
                    VALUES('{IdDiscord}', '{Nickname}', '{TipoPerfil}', '1', '1', '{datetime.now()}');
                """)

                cur.execute(f"""SELECT id FROM usuario WHERE discord_id_user = '{IdDiscord}'""")
                idGeradoUsuario = cur.fetchone()[0]

                cur.execute(f"""
                    INSERT INTO ranqueamento(id_usuario,id_temporada, data_criacao, data_atualizacao)
                    VALUES ({idGeradoUsuario}, {temporadaAtual.Id}, '{datetime.now()}', '{datetime.now()}')
                """)

                cur.execute(f"""
                    INSERT INTO FICHA (id_usuario, id_corpo, data_criacao) values
                    ({idGeradoUsuario}, {produtosFichaCorpo[0].Id}, '{datetime.now()}')
                """)

                Retorno.resultado = f"{Nickname} foi registrado como {TipoPerfil}!"
            else:
                Retorno.resultado = "Usuário já registrado."

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

    def SairOuVoltarDoEvento(self, IdDiscord):
        Retorno = DBResultado()
        pesquisa = None
        dataAtual = datetime.now()
        temporadaAtual = self.tabelasDominioDB.GetTemporadaAtual()
        numeroAndares = self.tabelasDominioDB.GetNumeroDeAndaresAtual()
        conn = psycopg2.connect(self.connectionString)
        cur = conn.cursor()
        try:
            cur.execute(f"""
                SELECT usuario.id, usuario.discord_id_user, usuario.ativo, ranqueamento.power FROM usuario 
                JOIN ranqueamento on ranqueamento.id_usuario = usuario.id
                WHERE discord_id_user = '{IdDiscord}';""")
            pesquisa = cur.fetchone()

            if(pesquisa != None):
                if(pesquisa[2] == '1'):
                    cur.execute(f"""
                            SELECT id from historico_partidas WHERE (id_usuario_desafiante = {pesquisa[0]} or id_usuario_desafiado = {pesquisa[0]})
                            and estado_partida = {Mensagens.EP_AGUARDANDO}
                        """)
                    possuiPartidaPendente = cur.fetchone()

                    print(possuiPartidaPendente)
                    if(possuiPartidaPendente != None):
                        Retorno.corResultado = Cores.Alerta
                        Retorno.resultado =  f"""
                            ⚠️⚠️⚠️⚠️ <@{IdDiscord}> \n ## AINDA HÁ DESAFIOS PENDENTES DE CONCLUSÃO! NÃO DA PRA SAIR! \n ⚠️⚠️⚠️⚠️
                            """
                        cur.close()
                        conn.close()    
                        return Retorno
                    
                    cur.execute(f"""
                        UPDATE 
                            usuario set ativo = '0' 
                            WHERE ativo = '1' and id = {pesquisa[0]};

                        UPDATE
                            ranqueamento set
                                power = 0
                                vitorias_consecutivas = 0
                            WHERE id_usuario = {pesquisa[0]} and
                            id_temporada = {temporadaAtual.Id} 
                        """)

                    Retorno.resultado = "Saiu com sucesso."
                if(pesquisa[2] == '0'):
                    cur.execute(f"""
                        UPDATE usuario set ativo = '1' where ativo = '0' and id = {pesquisa[0]};
                    """)
                    Retorno.resultado = "Retornou! Bem vindo de volta!"
            else:
                Retorno.resultado = "Usuário não encontrado."

            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            cur.close()
            conn.close()
            Retorno.resultado += "Ocorreu um erro: \n" + str(traceback.format_exc())
            Retorno.corResultado = Cores.Erro

        return Retorno

    def ListarUsuarios(self, nome = None):
        Retorno = DBResultado()
        jogadores = []
        try:
            conn = psycopg2.connect(self.connectionString)
            cur = conn.cursor()

            stringQueryUsuarios = f"""
                    SELECT u.nome, r.power, u.tipo_perfil, u.ativo, u.pontos
                    FROM usuario u
                    JOIN ranqueamento r on id_usuario = u.id  
                    $WHERE
                    order by r.power ASC, ativo DESC, tipo_perfil DESC 
                    """
            if not nome or nome.isspace():
                cur.execute(stringQueryUsuarios.replace('$WHERE', ''))
            else:
                cur.execute(stringQueryUsuarios.replace(
                    '$WHERE',
                    f"WHERE usuario.nome like '%{nome}%'"
                ))

            usuarios = cur.fetchall()
            for usuario in usuarios:
                nomeJogador = f"† {usuario[0].lower()}" if usuario[3] == '0' else usuario[0].upper()
                nomeJogador = f"★ {nomeJogador}" if usuario[2] == Mensagens.U_ORGANIZADOR else nomeJogador

                novoJogador = [nomeJogador, usuario[1], usuario[4]]
                jogadores.append(novoJogador)
                if(len(jogadores) > 30): break

            output = t2a(
                header=["Nome", "P", "CS"],
                body=jogadores,
                style=PresetStyle.thin_compact
            )
            print(output)
            Retorno.resultado += f"""\n{output}\n Total de jogadores: {len(usuarios)}"""

            cur.close()
            conn.close()
            
            Retorno.corResultado = Cores.Sucesso
        except Exception as e:
            Retorno.resultado += "Ocorreu um erro: \n" + str(traceback.format_exc())
            Retorno.corResultado = Cores.Erro
        return Retorno

    def AtualizarTipoPerfil(self, IdDiscord, Nickname):
        Retorno = DBResultado()
        search = None
        conn = psycopg2.connect(self.connectionString)
        cur = conn.cursor()
        try:
            cur.execute(f"SELECT tipo_perfil FROM usuario WHERE discord_id_user = '{IdDiscord}' AND nome = '{Nickname}';")
            
            search = cur.fetchone()

            if(search != None):
                if(search[0] == Mensagens.U_JOGADOR):
                    cur.execute(f"""
                        UPDATE usuario set tipo_perfil = '{Mensagens.U_ORGANIZADOR}' 
                        where tipo_perfil = '{Mensagens.U_JOGADOR}' AND discord_id_user = '{IdDiscord}';
                    """)
                    Retorno.resultado = f"Sucesso! {Nickname} foi atualizado para {Mensagens.U_ORGANIZADOR}"
                elif(search[0] == Mensagens.U_ORGANIZADOR):
                    cur.execute(f"""
                        UPDATE usuario set tipo_perfil = '{Mensagens.U_JOGADOR}' 
                        where tipo_perfil = '{Mensagens.U_ORGANIZADOR}' AND discord_id_user = '{IdDiscord}';
                    """)
                    Retorno.resultado = f"Sucesso! {Nickname} foi atualizado para {Mensagens.U_JOGADOR}"
                
            else:
                Retorno.resultado = f"O usuário informado não foi encontrado."

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

    def GetPartidasUsuario(self, IdDiscord, token):
        Retorno = DBResultado()
        historicoPartidas = []
        textoResultado = ''
        try:
            conn = psycopg2.connect(self.connectionString)
            cur = conn.cursor()

            query = f"""
                SELECT 
                u.nome as desafiante, u2.nome as desafiado, 
                hp.usuario_desafiante_vitorias, hp.usuario_desafiado_vitorias, hp.id_usuario_vencedor, hp.estado_partida,
                hp.data_criacao, hp.token
                FROM historico_partidas hp 
                JOIN usuario u on hp.id_usuario_desafiante = u.id 
                JOIN usuario u2 on hp.id_usuario_desafiado = u2.id
                WHERE (u.discord_id_user = '{IdDiscord}' or u2.discord_id_user='{IdDiscord}') $WHERE
                ORDER by 
                CASE when hp.estado_partida = '{Mensagens.EP_EXPIRADO}' then 1 else 0 end, 
                CASE when hp.estado_partida = '{Mensagens.EP_JOGADOR_AUSENTE}' then 1 else 0 end,
                hp.estado_partida,
                hp.data_criacao DESC
            """

            if not token or token.isspace():
                cur.execute(query.replace('$WHERE', ''))
            else:
                cur.execute(query.replace("$WHERE",f"""and token like '%{token}%'"""))
              
            historicoPesquisa = cur.fetchall()

            for partida in historicoPesquisa:
                vitoriasDesafiante = partida[2] if partida[2] != None else "-"
                vitoriasDesafiado = partida[3] if partida[3] != None else "-"
                dataCriacaoFormatada = f'{partida[6].day}/{partida[6].month}/{partida[6].year}'
                novaPartida = [partida[0].upper(), vitoriasDesafiante, vitoriasDesafiado, partida[1].upper(), partida[5], partida[7].replace("gensou-", ""), dataCriacaoFormatada]
                historicoPartidas.append(novaPartida)
                if(len(historicoPartidas) > 10): break

            output = t2a(
                header=["Desafiante","Wins", "Wins", "Desafiado", "Estado", "Token", "Criado"],
                body=historicoPartidas,
                style=PresetStyle.thin_compact
            )
            print(output)
            
            Retorno.resultado = f"""{output}\nTotal de partidas: {len(historicoPesquisa)}"""

            Retorno.corResultado = Cores.Sucesso
            cur.close()
            conn.close()
        except Exception as e:
            cur.close()
            conn.close()
            Retorno.resultado += "Ocorreu um erro: \n" + str(traceback.format_exc())
            Retorno.corResultado = Cores.Erro
        return Retorno

    def GetPartidas(self, token):
        Retorno = DBResultado()
        historicoPartidas = []
        textoResultado = ''
        try:
            conn = psycopg2.connect(self.connectionString)
            cur = conn.cursor()

            query = f"""
                SELECT 
                u.nome as desafiante, u2.nome as desafiado, 
                hp.usuario_desafiante_vitorias, hp.usuario_desafiado_vitorias, hp.id_usuario_vencedor, hp.estado_partida,
                hp.data_criacao, hp.token
                FROM historico_partidas hp 
                JOIN usuario u on hp.id_usuario_desafiante = u.id 
                JOIN usuario u2 on hp.id_usuario_desafiado = u2.id
                $WHERE
                ORDER by 
                CASE when hp.estado_partida = '{Mensagens.EP_EXPIRADO}' then 1 else 0 end, 
                CASE when hp.estado_partida = '{Mensagens.EP_JOGADOR_AUSENTE}' then 1 else 0 end,
                hp.estado_partida,
                hp.data_criacao DESC
            """
            if not token or token.isspace():
                cur.execute(query.replace("$WHERE",""))
            else:
                cur.execute(query.replace("$WHERE",f"""WHERE token like '%{token}%'"""))

            historicoPesquisa = cur.fetchall()

            for partida in historicoPesquisa:
                vitoriasDesafiante = partida[2] if partida[2] != None else "-"
                vitoriasDesafiado = partida[3] if partida[3] != None else "-"
                dataCriacaoFormatada = f'{partida[6].day}/{partida[6].month}/{partida[6].year}'
                novaPartida = [partida[0].upper(), vitoriasDesafiante, vitoriasDesafiado, partida[1].upper(), partida[5], partida[7].replace("gensou-", ""), dataCriacaoFormatada]
                historicoPartidas.append(novaPartida)
                if(len(historicoPartidas) > 10): break

            output = t2a(
                header=["Desafiante","V", "V", "Desafiado", "Estado", "Token", "Criado"],
                body=historicoPartidas,
                style=PresetStyle.thin_compact
            )
            
            print(output)
            Retorno.resultado = f"""{output}\nTotal de partidas: {len(historicoPesquisa)}"""
            Retorno.corResultado = Cores.Sucesso
            cur.close()
            conn.close()
        except Exception as e:
            cur.close()
            conn.close()
            Retorno.resultado += "Ocorreu um erro: \n" + str(traceback.format_exc())
            Retorno.corResultado = Cores.Erro
        return Retorno

    def GetUsuario(self, IdDiscord):
        Retorno = UsuarioDTO()
        pesquisa = ""
        conn = psycopg2.connect(self.connectionString)
        cur = conn.cursor()
        cur.execute(f"SELECT nome, ativo, dados_publicos, tipo_perfil FROM usuario WHERE discord_id_user = '{IdDiscord}'")

        pesquisa = cur.fetchone()
        if(pesquisa == None):
            cur.close()
            conn.close()
            return None

        Retorno.Nome = pesquisa[0]
        Retorno.Ativo = pesquisa[1]
        Retorno.DadosPublicos = pesquisa[2]
        Retorno.TipoPerfil = pesquisa[3]
        cur.close()
        conn.close()

        return Retorno

    def GetIdDiscordUsuariosPartida(self, token):
        Retorno = DBResultado()
        historicoPartidas = []
        textoResultado = ''
        try:
            conn = psycopg2.connect(self.connectionString)
            cur = conn.cursor()

            cur.execute(f"""          
                    SELECT 
                        u.discord_id_user as desafiante, u2.discord_id_user as desafiado
                        FROM historico_partidas hp 
                        JOIN usuario u on hp.id_usuario_desafiante = u.id 
                        JOIN usuario u2 on hp.id_usuario_desafiado = u2.id
                        WHERE hp.token like '%{token}'
                    """)

            idsJogadoresPartida = cur.fetchone()
            
            if(idsJogadoresPartida == None):
                cur.close()
                conn.close()
                Retorno.resultado = "Partida não encontrada."
                Retorno.corResultado = Cores.Alerta
                return Retorno
            
            Retorno.resultado = [idsJogadoresPartida[0], idsJogadoresPartida[1]]
            Retorno.corResultado = Cores.Sucesso
            cur.close()
            conn.close()
        except Exception as e:
            cur.close()
            conn.close()
            Retorno.resultado += "Ocorreu um erro: \n" + str(traceback.format_exc())
            Retorno.corResultado = Cores.Erro
        return Retorno
