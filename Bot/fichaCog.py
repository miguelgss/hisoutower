from discord.ext import commands
import discord

from DomainBD import UsuarioSql
from DomainGeneral import JogadorInputDTO

class Ficha(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.usuariosDB = UsuarioSql()

    @commands.command(
        brief=f'Retorna uma ficha informativa do usuário.', 
        description='Retorna uma ficha informativa do usuário.',
        aliases = ['mf','ficha','minhaficha'])
    async def MinhaFicha(self, ctx):
        jogadorInput = JogadorInputDTO()
        jogadorInput.Avatar = ctx.message.author.avatar
        jogadorInput.Nome = ctx.message.author.display_name
        jogadorInput.IdDiscord = ctx.message.author.id
        resultado = await self.usuariosDB.ObterPerfil(jogadorInput)
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