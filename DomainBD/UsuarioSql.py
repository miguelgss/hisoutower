from .PostgreSqlConn import PostgreSqlConn
import psycopg2
import traceback
from datetime import datetime, timedelta
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
        menorAndar = None
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
                cur.execute(f"""SELECT id FROM andar order by id desc""")
                menorAndar = cur.fetchone()[0]
                cur.execute(f"""SELECT id FROM usuario WHERE discord_id_user = '{IdDiscord}'""")
                idGeradoUsuario = cur.fetchone()[0]

                cur.execute(f"""
                    INSERT INTO ranqueamento(id_usuario,id_temporada, id_andar_atual, data_criacao, data_atualizacao, partidas_para_subir, partidas_para_descer, vitorias_consecutivas)
                    VALUES ({idGeradoUsuario}, {temporadaAtual.Id}, {menorAndar}, '{datetime.now()}', '{datetime.now()}', 2, 2, 0)
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
                SELECT usuario.id, usuario.discord_id_user, usuario.ativo, ranqueamento.id_andar_atual FROM usuario 
                JOIN ranqueamento on ranqueamento.id_usuario = usuario.id
                WHERE discord_id_user = '{IdDiscord}';""")
            pesquisa = cur.fetchone()

            if(pesquisa != None):
                if(pesquisa[2] == '1'):
                    cur.execute(f"""
                            SELECT id from historico_partidas where id_usuario_desafiante = {pesquisa[0]} or id_usuario_desafiado = {pesquisa[0]}
                            and id_estado_partida = 1
                        """)
                    possuiPartidaPendente = cur.fetchone()

                    if(possuiPartidaPendente != None):
                        Retorno.corResultado = Cores.Alerta
                        Retorno.resultado =  f"""
                            ⚠️⚠️⚠️⚠️ <@{IdDiscord}> \n ## AINDA HÁ DESAFIOS PENDENTES DE CONCLUSÃO! NÃO DA PRA SAIR! \n ⚠️⚠️⚠️⚠️
                            """
                        cur.close()
                        conn.close()    
                        return Retorno
                    if(pesquisa[3] < 6):
                        cur.execute(f"""
                                SELECT ranqueamento.id, ranqueamento.id_andar_atual FROM ranqueamento
                                JOIN usuario on usuario.id = ranqueamento.id_usuario 
                                WHERE usuario.ativo = '1' and 
                                ranqueamento.id_andar_atual > {pesquisa[3]} and 
                                ranqueamento.id_andar_atual < 6 and 
                                ranqueamento.id_temporada = {temporadaAtual.Id} 
                                order by ranqueamento.id desc;
                            """)

                        jogadoresPromovidos = cur.fetchall()

                        for jgdPromovido in jogadoresPromovidos:
                            cur.execute(f"""
                                UPDATE ranqueamento SET
                                id_andar_atual = {jgdPromovido[1]-1},
                                data_atualizacao = '{dataAtual}'
                                WHERE id = {jgdPromovido[0]} and
                                id_temporada = {temporadaAtual.Id} 
                            """)
                    
                    cur.execute(f"""
                        UPDATE 
                            usuario set ativo = '0' 
                            WHERE ativo = '1' and id = {pesquisa[0]};

                        UPDATE
                            ranqueamento set
                                id_andar_atual = {numeroAndares},
                                partidas_para_subir = 2,
                                partidas_para_descer = 2,
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
        try:
            conn = psycopg2.connect(self.connectionString)
            cur = conn.cursor()

            if not nome or nome.isspace():
                cur.execute(f"""
                    SELECT usuario.nome, tipo_perfil, ativo, dados_publicos, a.id, r.partidas_para_subir
                    FROM usuario
                    JOIN ranqueamento r on id_usuario = usuario.id  
                    JOIN andar a on a.id = r.id_andar_atual  
                    """)
            else:
                cur.execute(f"""
                    SELECT usuario.nome, tipo_perfil, ativo, dados_publicos, a.id, r.partidas_para_subir
                    FROM usuario
                    JOIN ranqueamento r on id_usuario = usuario.id  
                    JOIN andar a on a.id = r.id_andar_atual 
                    WHERE position('{nome}' in usuario.nome) > 0
                """)

            usuarios = cur.fetchall()
            for usuario in usuarios:
                ativo = 'Ativo' if usuario[2] == '1' else 'Inativo'
                andarAtual = Mensagens.LISTA_ANDARES_CAIXA_ALTA[usuario[4]-1]
                Retorno.resultado += f'''- {usuario[0]: <12};{usuario[1]: <8};{ativo:<5};R: {andarAtual}; ToUp: {usuario[5]} \n'''

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

            if not token or token.isspace():
                cur.execute(f"""          
                    SELECT 
                        u.nome as desafiante, u2.nome as desafiado, 
                        hp.usuario_desafiante_vitorias, hp.usuario_desafiado_vitorias, hp.id_usuario_vencedor, ep.nome,
                        hp.data_criacao, hp.token
                        FROM historico_partidas hp 
                        JOIN usuario u on hp.id_usuario_desafiante = u.id 
                        JOIN usuario u2 on hp.id_usuario_desafiado = u2.id
                        JOIN estado_partida ep on hp.id_estado_partida = ep.id 
                        WHERE u.discord_id_user = '{IdDiscord}' or u2.discord_id_user='{IdDiscord}'
                        ORDER BY hp.id DESC
                        LIMIT 30
                    """)
            else:
                cur.execute(f"""          
                    SELECT 
                        u.nome as desafiante, u2.nome as desafiado, 
                        hp.usuario_desafiante_vitorias, hp.usuario_desafiado_vitorias, hp.id_usuario_vencedor, ep.nome,
                        hp.data_criacao, hp.token
                        FROM historico_partidas hp 
                        JOIN usuario u on hp.id_usuario_desafiante = u.id 
                        JOIN usuario u2 on hp.id_usuario_desafiado = u2.id
                        JOIN estado_partida ep on hp.id_estado_partida = ep.id 
                        WHERE u.discord_id_user = '{IdDiscord}' or u2.discord_id_user='{IdDiscord}' and position('{token}' in hp.token) > 0
                        ORDER BY hp.id DESC
                        LIMIT 30
                    """)                    

            historicoPartidas = cur.fetchall()

            for partida in historicoPartidas:
                vitoriasDesafiante = partida[2] if partida[2] != None else "-"
                vitoriasDesafiado = partida[3] if partida[3] != None else "-"
                dataCriacaoFormatada = f'{partida[6].day}/{partida[6].month}/{partida[6].year}'

                textoResultado += f'- {partida[0]}[{vitoriasDesafiante}] X [{vitoriasDesafiado}]{partida[1]} | {partida[5]} | {partida[7]} | {dataCriacaoFormatada} \n'

            Retorno.resultado = textoResultado
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

            if not token or token.isspace():
                cur.execute(f"""          
                    SELECT 
                        u.nome as desafiante, u2.nome as desafiado, 
                        hp.usuario_desafiante_vitorias, hp.usuario_desafiado_vitorias, hp.id_usuario_vencedor, ep.nome,
                        hp.data_criacao, hp.token
                        FROM historico_partidas hp 
                        JOIN usuario u on hp.id_usuario_desafiante = u.id 
                        JOIN usuario u2 on hp.id_usuario_desafiado = u2.id
                        JOIN estado_partida ep on hp.id_estado_partida = ep.id 
                        ORDER BY hp.id DESC
                        LIMIT 30
                    """)
            else:
                cur.execute(f"""          
                    SELECT 
                        u.nome as desafiante, u2.nome as desafiado, 
                        hp.usuario_desafiante_vitorias, hp.usuario_desafiado_vitorias, hp.id_usuario_vencedor, ep.nome,
                        hp.data_criacao, hp.token
                        FROM historico_partidas hp 
                        JOIN usuario u on hp.id_usuario_desafiante = u.id 
                        JOIN usuario u2 on hp.id_usuario_desafiado = u2.id
                        JOIN estado_partida ep on hp.id_estado_partida = ep.id 
                        WHERE position('{token}' in hp.token) > 0
                        ORDER BY hp.id DESC
                        LIMIT 30
                    """)

            historicoPartidas = cur.fetchall()

            for partida in historicoPartidas:
                vitoriasDesafiante = partida[2] if partida[2] != None else "-"
                vitoriasDesafiado = partida[3] if partida[3] != None else "-"
                dataCriacaoFormatada = f'{partida[6].day}/{partida[6].month}/{partida[6].year}'

                textoResultado += f'- {partida[0]}[{vitoriasDesafiante}] X [{vitoriasDesafiado}]{partida[1]} | {partida[5]} | {partida[7]} | {dataCriacaoFormatada} \n'

            Retorno.resultado = textoResultado
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
