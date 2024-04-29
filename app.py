from flask_openapi3 import OpenAPI, Info, Tag
from flask import redirect
from urllib.parse import unquote

from sqlalchemy.exc import IntegrityError

from models import Session, Produto, Comentario
from logger import logger
from schemas import *
from flask_cors import CORS

info = Info(title="Minha API", version="1.0.0")
app = OpenAPI(__name__, info=info)
CORS(app)


home_tag = Tag(name="Documentação", description="Seleção de documentação: Swagger, Redoc ou RapiDoc")
produto_tag = Tag(name="Produto", description="Adição, visualização e remoção de produtos à base")
comentario_tag = Tag(name="Comentario", description="Adição de um comentário à um produtos cadastrado na base")


@app.get('/', tags=[home_tag])
def home():

    return redirect('/openapi')

@app.post('/produto', tags=[produto_tag],
          responses={"200": ProdutoViewSchema, "409": ErrorSchema, "400": ErrorSchema})
def add_produto(form: ProdutoSchema):

    print(form)
    produto = Produto(
        nome=form.nome,
        preco=form.preco,
        descricao=form.descricao,
        marca=form.marca,
        categoria=form.categoria
    )
    logger.info(f"Adicionando produto de nome: '{produto.nome}'")
    try:
   
        session = Session()
        session.add(produto)
        session.commit()
        logger.info("Adicionado produto: %s"% produto)
        return apresenta_produto(produto), 200

    except IntegrityError as e:
        error_msg = "Produto de mesmo nome e marca já salvo na base :/"
        logger.warning(f"Erro ao adicionar produto '{produto.nome}', {error_msg}")
        return {"mesage": error_msg}, 409

    except Exception as e:
        error_msg = "Não foi possível salvar novo item :/"
        logger.warning(f"Erro ao adicionar produto '{produto.nome}', {error_msg}")
        return {"mesage": error_msg}, 400


@app.get('/produtos', tags=[produto_tag],
         responses={"200": ListagemProdutosSchema, "404": ErrorSchema})
def get_produtos():

    logger.info(f"Coletando produtos ")
   
    session = Session()

    produtos = session.query(Produto).all()

    if not produtos:

        return {"produtos": []}, 200
    else:
        logger.info(f"%d rodutos econtrados" % len(produtos))

        return apresenta_produtos(produtos), 200


@app.get('/produto', tags=[produto_tag],
         responses={"200": ProdutoViewSchema, "404": ErrorSchema})
def get_produto(query: ProdutoBuscaPorIDSchema):

    produto_id = query.id
    logger.info(f"Coletando dados sobre produto #{produto_id}")
    session = Session()
    produto = session.query(Produto).filter(Produto.id == produto_id).first()

    if not produto:
        error_msg = "Produto não encontrado na base :/"
        logger.warning(f"Erro ao buscar produto '{produto_id}', {error_msg}")
        return {"mesage": error_msg}, 404
    else:
        logger.info("Produto econtrado: %s" % produto)
        return apresenta_produto(produto), 200


@app.delete('/produto', tags=[produto_tag],
            responses={"200": ProdutoDelSchema, "404": ErrorSchema})
def del_produto(query: ProdutoBuscaPorIDSchema):

    produto_nome = unquote(unquote(query.nome))
    logger.info(f"Deletando dados sobre produto #{produto_nome}")
    session = Session()
    count = session.query(Produto).filter(Produto.nome == produto_nome).delete()
    session.commit()

    if count:
        logger.info(f"Deletado produto #{produto_nome}")
        return {"mesage": "Produto removido", "id": produto_nome}
    else:
        error_msg = "Produto não encontrado na base :/"
        logger.warning(f"Erro ao deletar produto #'{produto_nome}', {error_msg}")
        return {"mesage": error_msg}, 404


@app.get('/busca_produto', tags=[produto_tag],
         responses={"200": ListagemProdutosSchema, "404": ErrorSchema})
def busca_produto(query: ProdutoBuscaPorNomeSchema):

    termo = unquote(query.termo)
    logger.info(f"Fazendo a busca por nome com o termo: {termo}")
    session = Session()
    produtos = session.query(Produto).filter(Produto.nome.ilike(f"%{termo}%")).all()
    
    if not produtos:
        return {"produtos": []}, 200
    else:
        logger.info(f"%d rodutos econtrados" % len(produtos))
        return apresenta_produtos(produtos), 200


@app.post('/cometario', tags=[comentario_tag],
          responses={"200": ProdutoViewSchema, "404": ErrorSchema})
def add_comentario(form: ComentarioSchema):

    produto_id  = form.produto_id
    logger.info(f"Adicionando comentários ao produto #{produto_id}")
    session = Session()
    produto = session.query(Produto).filter(Produto.id == produto_id).first()

    if not produto:
        error_msg = "Produto não encontrado na base :/"
        logger.warning(f"Erro ao adicionar comentário ao produto '{produto_id}', {error_msg}")
        return {"mesage": error_msg}, 404

    texto = form.texto
    comentario = Comentario(texto)

    produto.adiciona_comentario(comentario)
    session.commit()

    logger.info(f"Adicionado comentário ao produto #{produto_id}")

    return apresenta_produto(produto), 200
