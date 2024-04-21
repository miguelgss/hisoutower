from random import randrange
from io import BytesIO
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps
from datetime import datetime, timedelta
import traceback


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
        try:
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
        except Exception as e:
            print(str(e))
            print(str(traceback.format_exc()))
        
    async def GerarCardDesafio(desafianteProfile, desafianteChar, desafiadoProfile, desafiadoChar):
        try:
            width = 724
            height = 408
            canvas = Image.new("RGBA", (width,height), (255, 255, 255, 0))

            desafianteCharArt = Image.open(f"Utils/assets/base_desafio/personagens/{desafianteChar}.png").convert("RGBA")
            desafiadoCharArt  = Image.open(f"Utils/assets/base_desafio/personagens/{desafiadoChar}.png").convert("RGBA")
            desafiadoCharArt = ImageOps.mirror(desafiadoCharArt)

            vS = Image.open(f"Utils/assets/base_desafio/icones/vs_icon.png").convert("RGBA")
            gensouLogo = Image.open(f"Utils/assets/base_desafio/icones/gensou_icon.png").convert("RGBA")

            fichaDesafiante = Image.open(desafianteProfile)
            fichaDesafiado = Image.open(desafiadoProfile)

            canvas.paste(desafianteCharArt, (0, 0), desafianteCharArt)
            canvas.paste(desafiadoCharArt, (0,0), desafiadoCharArt)
            canvas.paste(fichaDesafiante, (((width//2)-210),0)  , fichaDesafiante)
            canvas.paste(fichaDesafiado,  (((width//2)-210),height-150), fichaDesafiado)
            canvas.paste(vS, (0,0), vS)
            canvas.paste(gensouLogo, (0,0), gensouLogo)
            
            retorno = None
            img = BytesIO()
            canvas.save(img, "PNG")
            img.seek(0)
            return img
        except Exception as e:
            print(str(e))
            print(str(traceback.format_exc()))
