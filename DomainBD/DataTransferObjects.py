class DBResultado():
    resultado = ""
    arquivo = None
    corResultado = None

class DBResultadoAtualizacaoPontos(DBResultado):
    vP_antes = 0
    vP_dps = 0
    dP_antes = 0
    dP_dps = 0

class UsuarioDTO():
    IdDiscord = None
    Nome = ''
    Ativo = ''
    DadosPublicos = ''
    TipoPerfil = ''

class EstadoPartidaDTO():
    Id = None
    Nome = ''

class TipoAtualizacaoDTO():
    Id = None
    Nome = ''

class TemporadaDTO():
    Id = None
    Nome = ''
    TemporadaAtiva = False

class ProdutoDTO():
    Id = None
    Nome = ''
    TipoProduto = ''

class AndarDTO():
    Id = None
    Nome = ''
    MinimoPoints = 0
    Ativo = False
    DataCriacao = None
    Boss = False

class FichaDTO():
    Id = None
    IdUsuario = None
    NomeUsuario = None
    IdCorpo = None
    CorpoNome = None
    IdBordaCorpo = None
    BordaCorpoNome = None