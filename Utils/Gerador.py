from random import randrange
from io import BytesIO
from PIL import Image, ImageChops, ImageDraw, ImageFont
from datetime import datetime, timedelta

class Gerador():
    def GerarToken():
        length = 6
        numbers = "0123456789"
        letters = "abcdefghijklmnopqrstuvwxyz"
        charsForPassword = numbers + letters
        password = ""
        while(length > 0):
            password += charsForPassword[randrange(len(charsForPassword))]
            length -= 1

        return f"gensou-{password}"

    async def GerarCardPerfil(jogador, tipoFicha, andarAtual, podeSubirDeRank, podeDescerDeRank):
        avatarSize = (62, 62)
        nome = str(jogador.display_name)

        template = Image.open(f"Utils/assets/botficha/base_ficha/{tipoFicha}.png").convert("RGBA")
        iconeRank = Image.open(f"Utils/assets/botficha/sprites/floor/{andarAtual}.png")
        upRank = Image.open(f"Utils/assets/botficha/sprites/rate/rateup.png")
        downRank = Image.open(f"Utils/assets/botficha/sprites/rate/ratedown.png")

        # Configura a foto do usuário
        picJogador = jogador.avatar
        dataJogador = BytesIO(await picJogador.read())
        picJogador = Image.open(dataJogador).convert("RGBA")
        picJogador = picJogador.resize(avatarSize, Image.ANTIALIAS).convert("RGBA")

        # Começa a "desenhar" o card do jogador
        draw = ImageDraw.Draw(template)

        # fontNome = ImageFont.truetype("Utils/assets/fonts/.ttf", 26)
        # fontAndar = ImageFont.truetype("Utils/assets/fonts/Lato-Regular.ttf", 12)
        fontNome = ImageFont.truetype("Utils/assets/fonts/spiegel.ttf", 30)
        fontAndar = ImageFont.truetype("Utils/assets/fonts/spiegel.ttf", 14)

        ascent, descent = fontNome.getmetrics()
        (width, baseline), (offset_x, offset_y) = fontNome.font.getsize(nome)

        draw.text((210-(width/2),8), nome, font=fontNome, fill=(255,255,255, 255), stroke_fill=(0,0,0,255), stroke_width=1)
        draw.text((110,66), andarAtual.upper(), font=fontAndar, fill=(255,255,255, 255), stroke_fill=(0,0,0,255), stroke_width=1)

        template.paste(picJogador, (21,31), picJogador)
        template.paste(iconeRank, (3,0), iconeRank)
        if(podeSubirDeRank):
            template.paste(upRank, (20, 0), upRank)
        if(podeDescerDeRank):
            template.paste(downRank, (20, 0), downRank)

        retorno = None
        img = BytesIO()
        template.save(img, "PNG")
        img.seek(0)
        return img
        
    async def GerarCardDesafio(desafiante, desafiado):
        dataExpiracao = datetime.now() + timedelta(days=3)
        textExpiracao = f"PRAZO: {dataExpiracao.day}/{dataExpiracao.month}/{dataExpiracao.year}"
        
        avatarSize = (145, 145)
        nomeDesafiante = str(desafiante.display_name)
        nomeDesafiado = str(desafiado.display_name)

        nomeDesafiante = f"{nomeDesafiante[:10]}..." if len(nomeDesafiante) > 16 else nomeDesafiante
        nomeDesafiado = f"{nomeDesafiado[:10]}..." if len(nomeDesafiado) > 16 else nomeDesafiado

        template = Image.open("Utils/assets/template-prototipo-vs.png").convert("RGBA")

        pfpDesafiante = desafiante.avatar
        dataDesafiante = BytesIO(await pfpDesafiante.read())
        pfpDesafiante = Image.open(dataDesafiante).convert("RGBA")

        pfpDesafiado = desafiado.avatar
        dataDesafiado = BytesIO(await pfpDesafiado.read())
        pfpDesafiado = Image.open(dataDesafiado).convert("RGBA")

        pfpDesafiante = pfpDesafiante.resize(avatarSize, Image.ANTIALIAS).convert("RGBA")
        pfpDesafiado = pfpDesafiado.resize(avatarSize, Image.ANTIALIAS).convert("RGBA")
        
        draw = ImageDraw.Draw(template)
        font = ImageFont.truetype("Utils/assets/Lato-Regular.ttf", 20)
        
        draw.text((210,46), nomeDesafiante, font=font, fill=0x741B47)
        draw.text((350,155), nomeDesafiado, font=font, fill=0x741B47)
        draw.text((210,190), textExpiracao, font=font, fill=0x741B47)
        
        template.paste(pfpDesafiante,(55,32),pfpDesafiante)
        template.paste(pfpDesafiado,(700-145-55,32),pfpDesafiado)
        
        retorno = None
        img = BytesIO()
        template.save(img, "PNG")
        img.seek(0)
        return img

    async def TesteImg():
        image = Image.new("RGB", (200,200), (0, 255, 255))
        bytes = BytesIO()
        image.save(bytes, format="PNG")
        bytes.seek(0)
        print(image)
        print(bytes)
        return bytes