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