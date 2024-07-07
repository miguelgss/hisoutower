from discord.ext import commands
import discord

from Utils import Mensagens, Cores, Gerador

from DomainBD import UsuarioSql

class Usuario(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.usuariosDB = UsuarioSql()

    @commands.command(
        brief=f'Se adiciona como {Mensagens.U_JOGADOR}', 
        description=f'Se adiciona ao hisoutower como {Mensagens.U_JOGADOR}, permitindo desafiar outros jogadores e participar do ranqueamento.',
        aliases = ['addme','am','adicioneme','meadicionar', 'meadiciona'])
    async def MeAdicionar(self, ctx):
        resultado = self.usuariosDB.RegisterUser(ctx.message.author.id, ctx.message.author.name, Mensagens.U_JOGADOR)
        await ctx.send(
            embed = discord.Embed(title=f"Adicionando...",
            description=resultado.resultado,
            color=resultado.corResultado)
        )

    @commands.command(
        brief=f'Lista os jogadores registrados de acordo com nome.', 
        description='Lista os jogadores registrados, incluindo se estão ativos e se permitem acesso ao seu histórico de partidas. Caso um nome seja informado, a pesquisa será filtrada.',
        aliases = ['lj','ljogador', 'ljogadores'])
    async def ListarJogadores(self, ctx, 
        nome:str = commands.parameter(default=None, description="Parâmetro que filtrará o resultado.")
        ):
        resultado = self.usuariosDB.ListarUsuarios(nome)
        if(resultado.corResultado == Cores.Sucesso):
            await ctx.send(f"""```{resultado.resultado}```""")
        else:
            await ctx.send(
                embed = discord.Embed(title=f"Jogadores:",
                description=f'''{resultado.resultado}''',
                color=resultado.corResultado)
            )

    @commands.command(
        brief=f'Lista as 10 partidas mais recentes do usuário.', 
        description='Lista as 10 partidas mais recentes do usuário.',
        aliases = ['hmp','mp', 'minhaspartidas', 'historicominhaspartidas'])
    async def HistoricoMinhasPartidas(
        self, ctx,
        token:str = commands.parameter(default=None, description="Parâmetro que filtrará o resultado.")
        ):
        resultado = self.usuariosDB.GetPartidasUsuario(ctx.author.id, token)
        if(resultado.corResultado == Cores.Sucesso):
            await ctx.send(f"""```{resultado.resultado}```""")
        else:
            await ctx.send(
                embed = discord.Embed(title=f"Meu histórico de partidas:",
                description=f'''{resultado.resultado}''',
                color=resultado.corResultado)
            )

    @commands.command(
        brief=f'Lista as 10 partidas mais recentes.', 
        description='Lista as 10 partidas mais recentes do sistema.',
        aliases = ['hp', 'historicopartidas', 'historico'])
    async def HistoricoPartidas(
        self, ctx,
        token:str = commands.parameter(default=None, description="Parâmetro que filtrará o resultado.")
        ):
        resultado = self.usuariosDB.GetPartidas(token)
        if(resultado.corResultado == Cores.Sucesso):
            await ctx.send(f"""```{resultado.resultado}```""")
        else:
            await ctx.send(
                embed = discord.Embed(title=f"Histórico de partidas:",
                description=f'''{resultado.resultado}''',
                color=resultado.corResultado)
            )
        
    @commands.command(
        brief=f'Retorna ou remove o usuário do evento.', 
        description='O usuário irá retornar para o evento caso esteja previamente desativado ou irá sair caso esteja participando. **Quando sair, seu ranqueamento será reiniciado para o menor possível.**',
        aliases = ['sve','sairvoltar', 'sair', 'voltar']
    )
    async def SairOuVoltarDoEvento(self, ctx):
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        usuario = None
        usuario = self.usuariosDB.GetUsuario(ctx.author.id)
        if(usuario == None):
            await ctx.send("Usuário não encontrado.")
            return
        if(usuario.Ativo == '1'):
            await ctx.send('Você está prestes a sair do evento, **O QUE FARÁ COM QUE VOCÊ PERCA SUA POSIÇÃO NO RANQUEAMENTO!** Se tiver certeza disso, digite "sim" ou "s".')
        else:
            await ctx.send('Bem vindo de volta ao evento! Para confirmar seu retorno, digite "sim" ou "s".')
        try:
            msg = await commands.wait_for('message', check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await ctx.send(f'Retorno/Saída de {ctx.author.name} cancelada. Favor tentar novamente.')
            return
        if(msg.content.lower() in ("sim", "s")):
            resultado = self.usuariosDB.SairOuVoltarDoEvento(ctx.author.id)
            if(resultado.corResultado == Cores.Sucesso):
                await ctx.send(
                    embed = discord.Embed(title=f"Saída/Retorno:",
                    description=f'''```{resultado.resultado}```''',
                    color=resultado.corResultado)
                )
            else:
                await ctx.send(
                    embed = discord.Embed(title=f"Saída/Retorno:",
                    description=f'''{resultado.resultado}''',
                    color=resultado.corResultado)
                )