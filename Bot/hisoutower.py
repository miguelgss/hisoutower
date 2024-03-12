# Importação de bibliotecas
import discord
import re
import json
import asyncio
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
    async def testeimg(ctx, user:discord.Member):
        img = await Gerador.GerarCardDesafio(ctx.author, user)
        try:
            file = discord.File(img, filename="profile.png")
            await ctx.send("...", file=file)
        except Exception as e:
            await ctx.send(str(e))
        img.close()
        

    @bot.command(
        brief=f'Se adiciona como {Mensagens.U_JOGADOR}', 
        description='Se adiciona ao hisoutower como {Mensagens.U_JOGADOR}, permitindo desafiar outros jogadores e participar do ranqueamento.',
        aliases = ['addme','am','adicioneme'])
    async def MeAdicionar(ctx):
        resultado = usuariosDB.RegisterUser(ctx.message.author.id, ctx.message.author.name, Mensagens.U_JOGADOR)
        await ctx.send(
            embed = discord.Embed(title=f"Adicionando...",
            description=resultado.resultado,
            color=resultado.corResultado)
        )

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
            description=f'''```{resultado.resultado}```''',
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
            await ctx.send('Você está prestes a sair do evento, **o que fará com que você perca seu posicionamento no ranqueamento.** Se tiver certeza disso, digite "sim" ou "s".')
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
        resultado = desafiosDB.Desafiar(ctx.author.id, user.id)
        await ctx.send(resultado.resultado)

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
        description='O resultado da partida será atualizado utilizando esse comando. **É NECESSÁRIO INFORMAR O TOKEN DA PARTIDA.**',
        aliases = ['rrp','rp', 'relatar', 'resultado', 'relatarResultado']
    )
    async def RelatarResultadoPartida(ctx, 
        token: str = commands.parameter(default=None, description="Token identificador da partida a ser atualizada."), 
        vitoriasDesafiante: int = commands.parameter(default=0, description="Vítorias do desafiante."), 
        vitoriasDesafiado: int = commands.parameter(default=0, description="Vitórias do desafiado.")):
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
            embed = discord.Embed(title=f"Retorno:",
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
                description=f'De: {ctx.message.author.name}; Comando: {ctx.message.content}; \n\n' + str(error),
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

