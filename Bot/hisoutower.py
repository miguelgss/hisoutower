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

# Cogs
from .fichaCog import Ficha
from .desafioCog import Desafio
from .adminCog import Admin
from .usuarioCog import Usuario

intents = discord.Intents.default()
intents.message_content = True

help_command = commands.DefaultHelpCommand(
    arguments_heading = "Parâmetros do comando:",
    no_category = 'Geral'
)

activity = discord.Game(name="SOKUTOWER: Use ;help para ver os comandos!")

bot = commands.Bot(
    command_prefix=';', 
    intents=intents,
    help_command = help_command,
    activity=activity
    )

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
            txtActivity = f"SOKUTOWER: Use ;help para ver os comandos! | {datetime.now().strftime('%d/%m/%Y | %X')} \n {expirarPartidas.resultado}"
            print(txtActivity)
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

    ### - COMANDOS COM PERMISSIONAMENTO (ORGANIZADORES)

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
        asyncio.run(bot.add_cog(Ficha(bot)))
        asyncio.run(bot.add_cog(Desafio(bot)))
        asyncio.run(bot.add_cog(Admin(bot)))
        asyncio.run(bot.add_cog(Usuario(bot)))

        bot.run(TOKEN)
    except Exception as e:
        if isinstance(e, discord.errors.LoginFailure):
            print("Token inválido")
        else:
            print(e)

