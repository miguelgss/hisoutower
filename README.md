# Projeto de ladder automatizado não integrado - BOT Discord

- Comunicação com discord: A biblioteca [discordpy](https://discordpy.readthedocs.io/en/stable/index.html);
- Criação de fichas: A biblioteca [Pillow](https://pypi.org/project/pillow/);
- Acesso ao BD em postgre: A biblioteca [psycopb2](https://www.psycopg.org/docs/)
- Dados: O [Supabase](https://supabase.com/dashboard/) foi utilizado como opção gratuita de armazenamento dos dados em postgre.


# Ajudantes no projeto

### Gin
- Definiu as novas regras para o bot a partir do Htscada e também trabalhou no design (as fichas de desafio e de perfil dos jogadores);

### Comissão Organizadora Original (Do Htscada)
- Eduardo, Decarabia, Vibago, Kujibiki, Machii, Hester, Grief e sakuyalover.


# Sobre

**bothisoutower** é um projeto de ranqueamento manutenido automaticamente pelo Discord, sendo primariamente feito para o jogo Touhou 12.3 Hisoutensoku mas que pode ser aplicado a qualquer outro contexto. Nele é possível se cadastrar no sistema e desafiar outros jogadores subir no sistema de ranqueamento.

[Aqui está documentado o que inspirou esse projeto](https://sites.google.com/site/gensouarena/home/competi%C3%A7%C3%B5es/htscada?authuser=0). As regras do bot são diretamente inspiradas pelo que está escrito nesse documento, com algumas adaptações que vão ser melhor descritas quando o bot chegar num estado estável e funcional.

Caso tenha interesse em ver o bot na prática **(quando ele estiver pronto)**, acesse o [Gensou Arena!](https://discord.gg/eKHfY6T) É o servidor brasileiro dedicado ao Touhou 12.3 Hisoutensoku.

# Configuração

O BOT utiliza da biblioteca psycopg2 que conectará a um banco de dados PostgreSQL. O banco deve ser gerado de acordo com o script contido no repositório (será publicado na versão estável, com as regras de negócio bem definidas).

Para configurar o BOT, é necessário criar dois arquivos na raíz (no mesmo nível do arquivo "main.py"):
- config.txt (Para se conectar ao Bot do Discord)
	- token = tokenDoBot
- sqlsettings.txt
	- dbname = nomeDoBD
	- user = usuarioDoBD
	- password = senhaDoBD
	- host = hostDoBD
	- port = portDoBD


