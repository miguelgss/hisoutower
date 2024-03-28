from .PostgreSqlConn import PostgreSqlConn
import psycopg2
from datetime import datetime, timedelta
from Utils import Mensagens, Cores, Gerador

from .DataTransferObjects import DBResultado, UsuarioDTO

class UsuarioSql(PostgreSqlConn):
    def __init__(self):
        super(UsuarioSql, self).__init__()

    def RegisterUser(self, IdDiscord, Nickname, TipoPerfil):
        Retorno = DBResultado()
        resultado = None
        temporadaAtual = None
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
                cur.execute(f"""SELECT id FROM temporada""")
                temporadaAtual = cur.fetchone()[0]
                cur.execute(f"""SELECT id FROM andar order by id desc""")
                menorAndar = cur.fetchone()[0]
                cur.execute(f"""SELECT id FROM usuario WHERE discord_id_user = '{IdDiscord}'""")
                idGeradoUsuario = cur.fetchone()[0]

                cur.execute(f"""
                    INSERT INTO ranqueamento(id_usuario,id_temporada, id_andar_atual, data_criacao, data_atualizacao, partidas_para_subir)
                    VALUES ({idGeradoUsuario}, {temporadaAtual}, {menorAndar}, '{datetime.now()}', '{datetime.now()}', 2)
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
            Retorno.resultado += "Ocorreu um erro: \n" + str(e)
            Retorno.corResultado = Cores.Erro
            
        return Retorno

    def SairOuVoltarDoEvento(self, IdDiscord):
        Retorno = DBResultado()
        pesquisa = None
        conn = psycopg2.connect(self.connectionString)
        cur = conn.cursor()
        try:
            cur.execute(f"SELECT id, discord_id_user, ativo FROM usuario WHERE discord_id_user = '{IdDiscord}';")
            # INCLUIR VALIDAÇÃO DE TROCAR RANQUEAMENTO EM RELAÇÃO AO TOP 5
            # EXEMPLO: SE QUEM SAIR ESTIVER NA POSIÇÃO 4, PUXAR O NA POSIÇÃO 5 PARA ESSA POSIÇÃO
            pesquisa = cur.fetchone()
            if(pesquisa != None):
                if(pesquisa[2] == '1'):
                    cur.execute(f"""
                        UPDATE usuario set ativo = '0' where ativo = '1' and id = {pesquisa[0]};
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
            Retorno.resultado += "Ocorreu um erro: \n" + str(e)
            Retorno.corResultado = Cores.Erro

        return Retorno

    def ListarUsuarios(self, nome = None):
        Retorno = DBResultado()
        try:
            conn = psycopg2.connect(self.connectionString)
            cur = conn.cursor()

            if not nome or nome.isspace():
                cur.execute(f"SELECT nome, tipo_perfil, ativo, dados_publicos FROM usuario")
            else:
                cur.execute(f"SELECT nome, tipo_perfil, ativo, dados_publicos FROM usuario WHERE position('{nome}' in nome) > 0")

            usuarios = cur.fetchall()
            for usuario in usuarios:
                ativo = 'Ativo' if usuario[2] == '1' else 'Inativo'
                historico = 'público' if usuario[3] == '1' else 'privado'
                Retorno.resultado += f'''Nome:{usuario[0]: <12};{usuario[1]: <8};{ativo:<5};Histórico:{historico:<5}\n'''

            cur.close()
            conn.close()
            
            Retorno.corResultado = Cores.Sucesso
        except Exception as e:
            Retorno.resultado += "Ocorreu um erro: \n" + str(e)
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
            Retorno.resultado += "Ocorreu um erro: \n" + str(e)
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