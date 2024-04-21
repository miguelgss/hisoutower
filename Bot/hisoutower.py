# Importação de bibliotecas
import discord
import re
import json
import asyncio
import traceback
from datetime import datetime
from discord.ext import commands, tasks

# Importação arquivos locais
from DomainBD import DesafioSql, UsuarioSql, TabelasDominioSql, RotinasAutomaticas
from Utils import Mensagens, Cores, Gerador

intents = discord.Intents.default()
intents.message_content = True

help_command = commands.DefaultHelpCommand(
    arguments_heading = "Parâmetros do comando:",
    no_category = 'Comandos gerais'
)

bot = commands.Bot(
    command_prefix=';', 
    intents=intents,
    help_command = help_command)

def run_discord_bot():

    TOKEN = ''
    with open('config.txt') as f:
        for line in f:
            if re.search("token", line):
                TOKEN = line.split(' ')[2]
    rotinasDB = RotinasAutomaticas()
    desafiosDB = DesafioSql()
    usuariosDB = UsuarioSql()
    tabelasDominioDB = TabelasDominioSql()
    
    # Inicia o bot
    @bot.event
    async def on_ready():
        if not checkMatches.is_running():
            checkMatches.start()
        print("Bot ligado")

    @tasks.loop(seconds=3600)
    async def checkMatches():
        try:
            expirarPartidas = rotinasDB.ExpirarPartidas()
            txtActivity = f";help para usar comandos | {datetime.now().strftime('%X')} \n {expirarPartidas.resultado}"
            activity = discord.CustomActivity(txtActivity)
            await bot.change_presence(status=discord.Status.online, activity=activity)
        except Exception as e:
            print(e)
        
    @bot.command(
        brief='Teste conexão BD', 
        description='Comando para testar a conexão com o banco de dados',
        aliases=['teste','ping'])
    async def Teste(ctx):
        search = rotinasDB.TestConnection()
        
        await ctx.send(
            embed=discord.Embed(title=f"Teste...",
            description=search.resultado,
            color=search.corResultado)
        )
    
    @bot.command()
    async def testeimg(ctx, 
        user: discord.Member = commands.parameter(description="Nome ou ID do usuário que será desafiado.")):  
        retorno = await desafiosDB.GerarImagemDesafio(ctx.author, user)
        try:
            file = discord.File(retorno.arquivo, filename="profile.png")
            await ctx.send("...", file=file)
        except Exception as e:
            await ctx.send(str(e))
        retorno.arquivo.close()

    @bot.command(
        brief=f'Se adiciona como {Mensagens.U_JOGADOR}', 
        description=f'Se adiciona ao hisoutower como {Mensagens.U_JOGADOR}, permitindo desafiar outros jogadores e participar do ranqueamento.',
        aliases = ['addme','am','adicioneme'])
    async def MeAdicionar(ctx):
        resultado = usuariosDB.RegisterUser(ctx.message.author.id, ctx.message.author.name, Mensagens.U_JOGADOR)
        await ctx.send(
            embed = discord.Embed(title=f"Adicionando...",
            description=resultado.resultado,
            color=resultado.corResultado)
        )

    @bot.command(
        brief=f'Retorna uma ficha informativa do usuário.', 
        description='Retorna uma ficha informativa com a posição atual do usuário e se irá subir/descer de rank dependendo do resultado da próxima partida.',
        aliases = ['mf','ficha','minhaficha'])
    async def MinhaFicha(ctx,
            tipoFicha:str = commands.parameter(default='', description=f"Permite escolher entre as seguintes personagens: {Mensagens.LISTA_FICHA_PERSONAGENS}.")
        ):
        resultado = await usuariosDB.ObterPerfil(ctx.message.author, tipoFicha)
        if(resultado.arquivo == None):
            await ctx.send(
                embed = discord.Embed(title=f"Ocorreu algum imprevisto...",
                description=resultado.resultado,
                color=resultado.corResultado)
            )
        else:
            try:
                file = discord.File(resultado.arquivo, filename=f"ficha_{ctx.message.author.display_name}.png")
                await ctx.send("", file=file)
            except Exception as e:
                await ctx.send(str(e))

    @bot.command(
        brief=f'Lista os jogadores registrados de acordo com nome.', 
        description='Lista os jogadores registrados, incluindo se estão ativos e se permitem acesso ao seu histórico de partidas. Caso um nome seja informado, a pesquisa será filtrada.',
        aliases = ['lj','ljogador', 'ljogadores'])
    async def ListarJogadores(ctx, 
        nome:str = commands.parameter(default=None, description="Parâmetro que filtrará a resultado.")
        ):
        resultado = usuariosDB.ListarUsuarios(nome)
        await ctx.send(
            embed = discord.Embed(title=f"Jogadores:",
            description=f'''{resultado.resultado}''',
            color=resultado.corResultado)
        )

    @bot.command(
        brief=f'Lista as 30 partidas mais recentes do usuário.', 
        description='Lista as 30 partidas mais recentes do usuário.',
        aliases = ['hmp','mp', 'minhaspartidas', 'historicominhaspartidas'])
    async def HistoricoMinhasPartidas(ctx):
        resultado = usuariosDB.GetPartidasUsuario(ctx.author.id)
        await ctx.send(
            embed = discord.Embed(title=f"Histórico de partidas:",
            description=f'''{resultado.resultado}''',
            color=resultado.corResultado)
        )

    @bot.command(
        brief=f'Lista as 30 partidas mais recentes.', 
        description='Lista as 30 partidas mais recentes do sistema.',
        aliases = ['hp', 'historicopartidas', 'historico'])
    async def HistoricoPartidas(ctx):
        resultado = usuariosDB.GetPartidas()
        await ctx.send(
            embed = discord.Embed(title=f"Histórico de partidas:",
            description=f'''{resultado.resultado}''',
            color=resultado.corResultado)
        )
        
    @bot.command(
        brief=f'Retorna ou remove o usuário do evento.', 
        description='O usuário irá retornar para o evento caso esteja previamente desativado ou irá sair caso esteja participando. **Quando sair, seu ranqueamento será reiniciado para o menor possível.**',
        aliases = ['sve','sairvoltar', 'sair', 'voltar']
    )
    async def SairOuVoltarDoEvento(ctx):
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        usuario = None
        usuario = usuariosDB.GetUsuario(ctx.author.id)
        if(usuario == None):
            await ctx.send("Usuário não encontrado.")
            return
        if(usuario.Ativo == '1'):
            await ctx.send('Você está prestes a sair do evento, **O QUE FARÁ COM QUE VOCÊ PERCA SUA POSIÇÃO NO RANQUEAMENTO!** Se tiver certeza disso, digite "sim" ou "s".')
        else:
            await ctx.send('Bem vindo de volta ao evento! Para confirmar seu retorno, digite "sim" ou "s".')
        try:
            msg = await bot.wait_for('message', check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await ctx.send(f'Retorno/Saída de {ctx.author.name} cancelada. Favor tentar novamente.')
            return
        if(msg.content.lower() in ("sim", "s")):
            resultado = usuariosDB.SairOuVoltarDoEvento(ctx.author.id)
            await ctx.send(
                embed = discord.Embed(title=f"Saída/Retorno:",
                description=f'''```{resultado.resultado}```''',
                color=resultado.corResultado)
            )

    ### - DESAFIOS
    @bot.command(
        brief=f'Desafia o usuário informado.', 
        description='Desafia o usuário informado para uma partida. O prazo para sua finalização é de 72 horas (3 dias).',
        aliases = ['d','desafiar']
    )
    async def Desafiar(ctx, 
        user: discord.Member = commands.parameter(description="Nome ou ID do usuário que será desafiado.")):
        resultado = await desafiosDB.Desafiar(ctx.author, user)
        if(resultado.corResultado == Cores.Sucesso):
            file = discord.File(resultado.arquivo, filename="profile.png")
            await ctx.send(
                resultado.resultado,
                file=file
            )
        else:
            await ctx.send(
                embed = discord.Embed(title=f"Ocorreu algum erro no desafio...",
                description=f'''{resultado.resultado}''',
                color=resultado.corResultado)
            )

    @bot.command(
        brief=f'Recusa a partida informada por token.', 
        description='Recusa a partida especificada pelo token. Só é possível recusar desafios de membros em andares superiores ou que já tenham jogado com o desafiador nas últimas 72h.',
        aliases = ['rd','recusar']
    )
    async def Recusar(ctx, 
        token: str = commands.parameter(description="Token identificador da partida a ser recusada.")):
        resultado = desafiosDB.RecusarDesafio(token, ctx.author.id)
        await ctx.send(
            embed = discord.Embed(title="Resultado da recusa:",
            description=f'''{resultado.resultado}''',
            color=resultado.corResultado)
        )


    ### - COMANDOS COM PERMISSIONAMENTO (ORGANIZADORES)
    @bot.command(
        brief=f'Muda o usuário entre {Mensagens.U_JOGADOR} e {Mensagens.U_ORGANIZADOR}', 
        description=f'Atualiza o estado de um usuário informado de {Mensagens.U_JOGADOR} para {Mensagens.U_ORGANIZADOR} e vice versa. Caso nenhum seja informado, atualizará o tipo de perfil do autor que utilizou o comando.',
        aliases = ['atp','atualizartp', 'atualizartipoperfil']
    )
    @commands.has_any_role(*['teste1', 'Colaboradores', 'Gensou Administrator'])
    async def AtualizarTipoPerfil(
        ctx, 
        user: discord.Member = commands.parameter(default=None, description="Usuário que terá seu estado modificado.")
        ):
        membro = user
        if(not membro): 
            membro = ctx.author
        resultado = usuariosDB.AtualizarTipoPerfil(membro.id, membro.name)
        await ctx.send(
            embed = discord.Embed(title=f"Atualizando tipo de perfil...",
            description=resultado.resultado,
            color=resultado.corResultado)
        )

    @bot.command(
        brief=f'Relata o resultado de uma partida.', 
        description='O resultado da partida será atualizado utilizando esse comando. **É NECESSÁRIO INFORMAR, EM ORDEM: TOKEN DA PARTIDA; VITORIAS DESAFIANTE; VITORIAS DESAFIADO.**',
        aliases = ['rrp','rp', 'relatar', 'resultado', 'relatarResultado']
    )
    async def RelatarResultadoPartida(ctx, 
        token: str = commands.parameter(description="Token identificador da partida a ser atualizada."), 
        vitoriasDesafiante: int = commands.parameter(description="Vítorias do desafiante.",), 
        vitoriasDesafiado: int = commands.parameter(description="Vitórias do desafiado.")):
        usuario = None
        usuario = usuariosDB.GetUsuario(ctx.author.id)
        if(usuario.TipoPerfil != Mensagens.U_ORGANIZADOR):
            await ctx.send(
            embed = discord.Embed(title=f"SEM PERMISSÃO!",
            description="É necessário ser um ORGANIZADOR para utilizar este comando.",
            color=Cores.Alerta)
            )
            return
        else:
            resultado = desafiosDB.RelatarResultado(token, vitoriasDesafiante, vitoriasDesafiado)
            await ctx.send(
            embed = discord.Embed(title=f"Resultado:",
            description=resultado.resultado,
            color=resultado.corResultado)
            )
        
    @bot.command(
        brief=f'Conclui uma partida que foi cancelada por expiração.', 
        description='Permite finalizar uma partida que foi cancelada por expiração. Caso a vitória e derrota sejam zero, será considerado empate. Caso a vitória de algum jogador seja informada, o posicionamento dos jogadores será atualizado de acordo. **É NECESSÁRIO INFORMAR, EM ORDEM: TOKEN DA PARTIDA; VITORIAS DESAFIANTE; VITORIAS DESAFIADO.**',
        aliases = ['cpe','concluir', 'concluirExpirada', 'concluirPartidaExpirada']
    )
    async def ConcluirPartidaExpirada(ctx, 
        token: str = commands.parameter(description="Token identificador da partida a ser atualizada."), 
        vitoriasDesafiante: int = commands.parameter(description="Vítorias do desafiante.",), 
        vitoriasDesafiado: int = commands.parameter(description="Vitórias do desafiado.")):
        usuario = None
        usuario = usuariosDB.GetUsuario(ctx.author.id)
        if(usuario.TipoPerfil != Mensagens.U_ORGANIZADOR):
            await ctx.send(
            embed = discord.Embed(title=f"SEM PERMISSÃO!",
            description="É necessário ser um ORGANIZADOR para utilizar este comando.",
            color=Cores.Alerta)
            )
            return
        else:
            resultado = desafiosDB.ConcluirPartidaExpirada(token, vitoriasDesafiante, vitoriasDesafiado)
            await ctx.send(
            embed = discord.Embed(title=f"Resultado:",
            description=resultado.resultado,
            color=resultado.corResultado)
            )
    ###--- HANDLER DE ERROS 
    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.errors.MissingAnyRole):
            await ctx.send(
                embed=discord.Embed(title="⚠️ Alerta:",
                description=f'De: {ctx.message.author}; Comando: {ctx.message.content}; \n\n' + Mensagens.SemPermissao,
                color=Cores.Alerta)
            )
        elif isinstance(error, commands.errors.CommandNotFound):
            await ctx.send(
                embed=discord.Embed(title="⚠️ Alerta:",
                description=f'De: {ctx.message.author}; Comando: {ctx.message.content}; \n\n' + Mensagens.ComandoNaoEncontrado,
                color=Cores.Alerta)
            )
        elif isinstance(error, commands.errors.MemberNotFound):
            await ctx.send(
                embed=discord.Embed(title="⚠️ Alerta:",
                description=f'De: {ctx.message.author}; Comando: {ctx.message.content}; \n\n' + Mensagens.UsuarioNaoEncontrado,
                color=Cores.Alerta)
            )
        else:
            await ctx.send(
                embed=discord.Embed(title="🚫 Erro:",
                description=f'De: {ctx.message.author.name}; Comando: {ctx.message.content}; \n\n' + "Erro:" + str(error) + "\n\n" + str(traceback.format_exc()),
                color=Cores.Erro)
            )
        print(str(error)) 

    try:
        bot.run(TOKEN)
    except Exception as e:
        if isinstance(e, discord.errors.LoginFailure):
            print("Token inválido")
        else:
            print(e)

