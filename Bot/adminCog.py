from discord.ext import commands
import discord

from Utils import Mensagens, Cores, Gerador

from DomainBD import DesafioSql, UsuarioSql

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.desafiosDB = DesafioSql()
        self.usuariosDB = UsuarioSql()

    @commands.command(
        brief=f'Muda o usuário entre {Mensagens.U_JOGADOR} e {Mensagens.U_ORGANIZADOR}', 
        description=f'Atualiza o estado de um usuário informado de {Mensagens.U_JOGADOR} para {Mensagens.U_ORGANIZADOR} e vice versa. Caso nenhum seja informado, atualizará o tipo de perfil do autor que utilizou o comando.',
        aliases = ['atp','atualizartp', 'atualizartipoperfil']
    )
    @commands.has_any_role(*['teste1', 'Colaboradores', 'Gensou Administrator'])
    async def AtualizarTipoPerfil(
        self,ctx, 
        user: discord.Member = commands.parameter(default=None, description="Usuário que terá seu estado modificado.")
        ):
        membro = user
        if(not membro): 
            membro = ctx.author
        resultado = self.usuariosDB.AtualizarTipoPerfil(membro.id, membro.name)
        await ctx.send(
            embed = discord.Embed(title=f"Atualizando tipo de perfil...",
            description=resultado.resultado,
            color=resultado.corResultado)
        )

    @commands.command(
        brief=f'Relata o resultado de uma partida.', 
        description='O resultado da partida será atualizado utilizando esse comando. **É NECESSÁRIO INFORMAR, EM ORDEM: TOKEN DA PARTIDA; VITORIAS DESAFIANTE; VITORIAS DESAFIADO.**',
        aliases = ['rrp','rp', 'relatarResultado']
    )
    async def RelatarResultadoPartida(self, ctx, 
        token: str = commands.parameter(description="Token identificador da partida a ser atualizada."), 
        vitoriasDesafiante: int = commands.parameter(description="Vítorias do desafiante.",), 
        vitoriasDesafiado: int = commands.parameter(description="Vitórias do desafiado.")):
        usuario = None
        usuario = self.usuariosDB.GetUsuario(ctx.author.id)
        if(usuario.TipoPerfil != Mensagens.U_ORGANIZADOR):
            await ctx.send(
            embed = discord.Embed(title=f"SEM PERMISSÃO!",
            description="É necessário ser um ORGANIZADOR para utilizar este comando.",
            color=Cores.Alerta)
            )
            return
        else:
            resultado = self.desafiosDB.RelatarResultado(token, vitoriasDesafiante, vitoriasDesafiado)
            await ctx.send(
            embed = discord.Embed(title=f"Resultado:",
            description=resultado.resultado,
            color=resultado.corResultado)
            )
        
    @commands.command(
        brief=f'Conclui uma partida que foi cancelada por expiração.', 
        description='Permite finalizar uma partida que foi cancelada por expiração. Caso a vitória e derrota sejam zero, será considerado empate. Caso a vitória de algum jogador seja informada, o posicionamento dos jogadores será atualizado de acordo. **É NECESSÁRIO INFORMAR, EM ORDEM: TOKEN DA PARTIDA; VITORIAS DESAFIANTE; VITORIAS DESAFIADO.**',
        aliases = ['cpe','concluir', 'concluirExpirada', 'concluirPartidaExpirada']
    )
    async def ConcluirPartidaExpirada(self, ctx, 
        token: str = commands.parameter(description="Token identificador da partida a ser atualizada."), 
        vitoriasDesafiante: int = commands.parameter(description="Vítorias do desafiante.",), 
        vitoriasDesafiado: int = commands.parameter(description="Vitórias do desafiado.")):
        usuario = None
        usuario = self.usuariosDB.GetUsuario(ctx.author.id)
        if(usuario.TipoPerfil != Mensagens.U_ORGANIZADOR):
            await ctx.send(
            embed = discord.Embed(title=f"SEM PERMISSÃO!",
            description="É necessário ser um ORGANIZADOR para utilizar este comando.",
            color=Cores.Alerta)
            )
            return
        else:
            resultado = self.desafiosDB.ConcluirPartidaExpirada(token, vitoriasDesafiante, vitoriasDesafiado)
            await ctx.send(
            embed = discord.Embed(title=f"Resultado:",
            description=resultado.resultado,
            color=resultado.corResultado)
            )