from discord.ext import commands
import discord

from Utils import Cores

from DomainBD import DesafioSql, UsuarioSql

class Desafio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.desafiosDB = DesafioSql()
        self.usuariosDB = UsuarioSql()

    @commands.command(
        brief=f'Desafia o usuário informado.', 
        description='Desafia o usuário informado para uma partida. O prazo para sua finalização é de 72 horas (3 dias).',
        aliases = ['d','desafiar']
    )
    async def Desafiar(self,ctx, 
        user: discord.Member = commands.parameter(description="Nome ou ID do usuário que será desafiado.")):
        resultado = await self.desafiosDB.Desafiar(ctx.author, user)
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

    @commands.command(
        brief=f'[DESENVOLVIMENTO] Desafia um usuário aleatório.', 
        description='[DESENVOLVIMENTO] Desafia um usuário aleatório. O prazo para finalização da partida é de 72 horas (3 dias).',
        aliases = ['hts','soku', 'tower', 'sokutower','da','desafiaraleatorio']
    )
    async def DesafiarAleatorio(self,ctx):
        await ctx.send(
            embed = discord.Embed(title=f"Em desenvolvimento...",
            description=f'''Fé no pai que esse comando sai''',
            color=resultado.corResultado)
        )

    @commands.command(
        brief=f'Recusa a partida informada por token.', 
        description='Recusa a partida especificada pelo token. Só é possível recusar desafios de membros em andares superiores ou que já tenham jogado com o desafiador nas últimas 72h.',
        aliases = ['r','recusar', 'refuse']
    )
    async def Recusar(self,ctx, 
        token: str = commands.parameter(description="Token identificador da partida a ser recusada.")):
        resultado = self.desafiosDB.RecusarDesafio(token, ctx.author.id)
        await ctx.send(
            embed = discord.Embed(title="Resultado da recusa:",
            description=f'''{resultado.resultado}''',
            color=resultado.corResultado)
        )

    @commands.command(
        brief=f'Permite aos jogadores concluírem as próprias partidas.', 
        description='Permite aos jogadores concluírem as próprias partidas. **É NECESSÁRIO INFORMAR, EM ORDEM: TOKEN DA PARTIDA; VITORIAS DESAFIANTE; VITORIAS DESAFIADO.**',
        aliases = ['fpj', 'fp', 'finalizar', 'finalizarpartidajogador', 'finalizarpartida']
    )
    async def FinalizarPartidaJogador(self,ctx,
        token: str = commands.parameter(description="Token identificador da partida a ser atualizada."), 
        vitoriasDesafiante: int = commands.parameter(description="Vítorias do desafiante.",), 
        vitoriasDesafiado: int = commands.parameter(description="Vitórias do desafiado.")):
        buscaJogadores = self.usuariosDB.GetIdDiscordUsuariosPartida(token)
        desafiante = buscaJogadores.resultado[0]
        desafiado = buscaJogadores.resultado[1]
        usuarioAceitador = None

        def check(m):
            return m.author == usuarioAceitador and m.channel == ctx.channel

        if(type(buscaJogadores.resultado) == list):
            if(str(ctx.author.id) in buscaJogadores.resultado):
                await ctx.send("É um dos jogadores dessa partida!")
                buscaJogadores.resultado.remove(str(ctx.author.id))
                usuarioAceitador = await self.bot.fetch_user(int(buscaJogadores.resultado[0]))

            else:
                await ctx.send("O usuário não é jogador da partida informada.")
                return

            await ctx.send(f'Resultado informado: <@{desafiante}> [{vitoriasDesafiante}] - [{vitoriasDesafiado}] <@{desafiado}>  para a partida de token {token}. Para confirmar o resultado, <@{usuarioAceitador.id}> deve digitar "sim" ou "s" em 30 segundos.')
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=31.0)
            except asyncio.TimeoutError:
                await ctx.send(f'O tempo de finalização da partida acabou. Favor tentar novamente.')
                return
            if(msg.content.lower() in ("sim", "s")):
                print("Aceitado!")
                resultado = self.desafiosDB.RelatarResultado(token, vitoriasDesafiante, vitoriasDesafiado)
                await ctx.send(
                embed = discord.Embed(title=f"Resultado:",
                description=resultado.resultado,
                color=resultado.corResultado)
                )
        else:
            await ctx.send(
            embed = discord.Embed(title="Ocorreu algum erro...",
            description=f'''{buscaJogadores.resultado}''',
            color=buscaJogadores.corResultado)
            )