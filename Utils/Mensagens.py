class Mensagens():
    UsuarioNaoEncontrado = "Usuário não encontrado."
    ComandoNaoEncontrado = "Comando não encontrado."
    SemPermissao = "Você não possui permissão para utilizar este comando."

    # Constantes:
    U_JOGADOR = "JOGADOR"
    U_ORGANIZADOR = "ORGANIZADOR"

    EP_AGUARDANDO = "AGUARDANDO"
    EP_RECUSADO = "RECUSADO_PELO_DESAFIANTE"
    EP_CONCLUIDO = "CONCLUÍDO"
    EP_CANCELADO = "CANCELADO_EXPIRACAO"
    EP_JOGADOR_AUSENTE = "VITORIA_JOGADOR_AUSENTE"
    EP_EMPATE = "EMPATE"

    TA_EXPIRACAO = "EXPIRACAO"

    A_CAMPEAO = "CAMPEÃO[TOPO]"
    A_PRIMEIRO = "PRIMEIRO[ELITE]"
    A_SEGUNDO = "SEGUNDO[ELITE]"
    A_TERCEIRO = "TERCEIRO[ELITE]"
    A_QUARTO = "QUARTO[ELITE]"

    LISTA_FICHA_PERSONAGENS = [
        "alice",
        "aya",
        "cirno",
        "iku",
        "komachi",
        "marisa",
        "meiling",
        "okuu",
        "patchy",
        "reimu",
        "reisen",
        "remilia",
        "sakuya",
        "sanae",
        "suika",
        "suwako",
        "tenshi",
        "youmu",
        "yukari",
        "yuyuko",
    ]

    LISTA_EP_FINALIZADA = [
        EP_RECUSADO,
        EP_CONCLUIDO,
        EP_CANCELADO,
        EP_JOGADOR_AUSENTE,
        EP_EMPATE
    ]

    LISTA_ICONES_ANDARES = [
        'campeao',
        'elite1',
        'elite2',
        'elite3',
        'elite4',
        'torre1',
        'torre2',
        'torre3'
    ]