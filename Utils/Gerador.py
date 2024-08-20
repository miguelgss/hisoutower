from random import randrange
from io import BytesIO
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps
from datetime import datetime, timedelta
import traceback
import math

from DomainGeneral import GerarFichaDTO

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

    async def GerarCardPerfil(inputFichaDto:GerarFichaDTO):
        try:
            avatarSize = (62, 62)
            nome = str(inputFichaDto.Nome)

            width = 420
            height = 150

            template = Image.open(f"Utils/assets/botficha/base_ficha/{inputFichaDto.TipoCorpo}.png").convert("RGBA")
            iconeRank = Image.open(f"Utils/assets/botficha/sprites/floor/{inputFichaDto.IdAndar}.png")
            iconePower = Image.open(f"Utils/assets/botficha/sprites/power.png").convert("RGBA")
            iconePontos = Image.open(f"Utils/assets/botficha/sprites/pontos.png").convert("RGBA")

            # Configura a foto do usuário
            picJogador = inputFichaDto.Avatar
            dataJogador = BytesIO(await picJogador.read())
            picJogador = Image.open(dataJogador).convert("RGBA")
            picJogador = picJogador.resize(avatarSize, Image.ANTIALIAS).convert("RGBA")

            # Começa a "desenhar" o card do jogador
            draw = ImageDraw.Draw(template)

            fontTamanhoNome = 32 if len(nome) < 20 else 16
            fontNome = ImageFont.truetype("Utils/assets/fonts/spiegel.ttf", fontTamanhoNome)
            fontAndar = ImageFont.truetype("Utils/assets/fonts/spiegel.ttf", 14)

            ascent, descent = fontNome.getmetrics()
            (widthf, baseline), (offset_x, offset_y) = fontNome.font.getsize(nome)

            stroke_text = (0,0,0,255)
            fill_text = (255, 255, 255, 255)

            draw.text((210-(widthf/2), math.fabs(fontTamanhoNome - 28)), nome, font=fontNome, fill=fill_text, stroke_fill=stroke_text, stroke_width=1)
            draw.text((110,66), inputFichaDto.NomeAndar.upper(), font=fontAndar, fill=fill_text, stroke_fill=stroke_text, stroke_width=1)

            pontos_w, pontos_h = draw.textsize(str(inputFichaDto.Pontos), font=fontAndar, direction="rtl")
            draw.text((32,height - pontos_h - 8), str(inputFichaDto.Power), font=fontAndar, fill=fill_text, stroke_fill=stroke_text, stroke_width=1)

            pontos_w, pontos_h = draw.textsize(str(inputFichaDto.Pontos), font=fontAndar, direction="rtl")
            draw.text(
                # (0, 0),  # top left corner
                # (width - text_w, 0), # top right corner
                (width - pontos_w - 16, height - pontos_h - 8), # bottom right corner
                # (0, height - text_h),  # bottom left corner
                # ((width - text_w) // 2, (height - text_h) // 2),  # center
                # (width - text_w, (height - text_h) // 2),  # center vertical + start from right
                str(inputFichaDto.Pontos),
                font=fontAndar,
                fill=fill_text,
                stroke_fill=stroke_text,
                stroke_width=1,
                direction='rtl',
                align='left',
            )

            template.paste(picJogador, (21,31), picJogador)
            template.paste(iconeRank, (3,0), iconeRank)
            template.paste(iconePontos, ((width - pontos_w - 32), (height - pontos_h - 8)), iconePontos)
            template.paste(iconePower, (16, (height - pontos_h - 8)), iconePower)

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

    async def GerarCardResultado(desafianteProfile, desafianteChar, desafiadoProfile, desafiadoChar, vitoriasDesafiante, vitoriasDesafiado):
        try:
            width = 724
            height = 408
            canvas = Image.new("RGBA", (width,height), (255, 255, 255, 0))

            desafianteCharType = "win" if vitoriasDesafiante == 4 else "loss"
            desafiadoCharType = "win" if vitoriasDesafiado == 4 else "loss"

            desafianteCharArt = Image.open(f"Utils/assets/base_desafio/{desafianteCharType}/{desafianteChar}.png").convert("RGBA") 
            desafiadoCharArt  = Image.open(f"Utils/assets/base_desafio/{desafiadoCharType}/{desafiadoChar}.png").convert("RGBA")
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
