from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from database import get_db, get_db_cursor, get_db_status, test_connection
from typing import List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Models Pydantic (mesmo código anterior)
class AgendamentoRequest(BaseModel):
    email: EmailStr
    data: str = Field(..., example="25/12/2024")
    hora: str = Field(..., example="14:30")
    servicos: List[int] = Field(..., min_items=1)

    @validator('data')
    def validar_data(cls, v):
        try:
            datetime.strptime(v, "%d/%m/%Y")
            return v
        except ValueError:
            raise ValueError("Data deve estar no formato DD/MM/AAAA")

    @validator('hora')
    def validar_hora(cls, v):
        try:
            datetime.strptime(v, "%H:%M")
            return v
        except ValueError:
            raise ValueError("Hora deve estar no formato HH:MM")


class UsuarioRequest(BaseModel):
    nome: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    senha: str = Field(..., min_length=6)
    telefone: str = Field(..., pattern=r'^[0-9]{10,11}$')


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str


class AgendamentoResponse(BaseModel):
    mensagem: str
    agendamento_id: int


class ServicoResponse(BaseModel):
    id: int
    nome: str
    preco: float
    descricao: str = None


app = FastAPI(
    title="API de Agendamentos",
    description="Sistema de gerenciamento de agendamentos e serviços",
    version="1.0.0"
)


# 🔹 Endpoint de status do sistema
@app.get("/status", tags=["Sistema"])
def status_sistema() -> Dict[str, Any]:
    """Verifica o status do sistema e banco de dados"""
    db_status = get_db_status()
    return {
        "api": "online",
        "database": db_status,
        "timestamp": datetime.now().isoformat()
    }


# 🔹 Redireciona para docs
@app.get("/", tags=["Home"])
def home() -> RedirectResponse:
    """Redireciona para a documentação interativa da API"""
    return RedirectResponse(url="/docs")


# 🔹 Teste do banco (melhorado)
@app.get("/teste-banco", tags=["Sistema"])
def teste_banco() -> Dict[str, Any]:
    """Endpoint para testar a conexão com o banco de dados"""
    try:
        if test_connection():
            return {
                "status": "conectado",
                "message": "Conexão com banco de dados estabelecida com sucesso",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Falha na conexão com banco de dados"
            )
    except Exception as e:
        logger.error(f"Erro no teste de banco: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Erro ao conectar ao banco: {str(e)}"
        )


# 🔹 Cadastro de usuário (usando context manager)
@app.post("/usuarios",
          status_code=status.HTTP_201_CREATED,
          tags=["Usuários"])
def criar_usuario(usuario: UsuarioRequest) -> Dict[str, str]:
    """Cria um novo usuário no sistema"""
    try:
        with get_db_cursor(dictionary=False) as cursor:
            # Verificar se email já existe
            cursor.execute("SELECT id FROM usuarios WHERE email = %s", (usuario.email,))
            if cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email já cadastrado"
                )

            cursor.execute(
                "INSERT INTO usuarios (nome, email, senha, telefone) VALUES (%s, %s, %s, %s)",
                (usuario.nome, usuario.email, usuario.senha, usuario.telefone)
            )
            logger.info(f"Usuário criado: {usuario.email}")
            return {"mensagem": "Usuário criado com sucesso"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar usuário: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro ao criar usuário. Verifique os dados informados."
        )


# 🔹 Login (usando context manager)
@app.post("/login", tags=["Autenticação"])
def login(login_data: LoginRequest) -> Dict[str, Any]:
    """Realiza login do usuário"""
    try:
        with get_db_cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT id, nome, email, telefone FROM usuarios WHERE email = %s AND senha = %s",
                (login_data.email, login_data.senha)
            )
            usuario = cursor.fetchone()

            if not usuario:
                logger.warning(f"Tentativa de login inválida para: {login_data.email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Email ou senha inválidos"
                )

            logger.info(f"Login realizado: {login_data.email}")
            return {"mensagem": "Login realizado com sucesso", "usuario": usuario}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar login"
        )


# 🔹 Listar serviços (usando context manager)
@app.get("/servicos",
         response_model=List[ServicoResponse],
         tags=["Serviços"])
def listar_servicos() -> List[Dict[str, Any]]:
    """Lista todos os serviços disponíveis"""
    try:
        with get_db_cursor(dictionary=True) as cursor:
            cursor.execute("SELECT id, nome, preco, descricao FROM servicos")
            servicos = cursor.fetchall()
            logger.info(f"{len(servicos)} serviços listados")
            return servicos
    except Exception as e:
        logger.error(f"Erro ao listar serviços: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao carregar serviços"
        )


# 🔹 Agendamento completo (usando context manager)
@app.post("/agendamentos",
          response_model=AgendamentoResponse,
          status_code=status.HTTP_201_CREATED,
          tags=["Agendamentos"])
def criar_agendamento(dados: AgendamentoRequest) -> Dict[str, Any]:
    """Cria um novo agendamento com os serviços selecionados"""
    try:
        with get_db_cursor(dictionary=False) as cursor:
            # Buscar usuário
            cursor.execute("SELECT id FROM usuarios WHERE email = %s", (dados.email,))
            usuario = cursor.fetchone()

            if not usuario:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuário não encontrado"
                )

            usuario_id = usuario[0]

            # Validar disponibilidade
            data_convertida = datetime.strptime(dados.data, "%d/%m/%Y").date()
            hora_convertida = datetime.strptime(dados.hora, "%H:%M").time()

            cursor.execute(
                "SELECT id FROM agendamentos WHERE data_agendamento = %s AND hora_agendamento = %s",
                (data_convertida, hora_convertida)
            )
            if cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Horário já ocupado. Escolha outro horário."
                )

            # Criar agendamento
            cursor.execute(
                "INSERT INTO agendamentos (usuario_id, data_agendamento, hora_agendamento) VALUES (%s, %s, %s)",
                (usuario_id, data_convertida, hora_convertida)
            )
            agendamento_id = cursor.lastrowid

            # Validar e inserir serviços
            servicos_validos = []
            for servico_id in dados.servicos:
                cursor.execute("SELECT id FROM servicos WHERE id = %s", (servico_id,))
                if cursor.fetchone():
                    servicos_validos.append(servico_id)

            if not servicos_validos:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Nenhum serviço válido encontrado"
                )

            # Inserir serviços relacionados
            for servico_id in servicos_validos:
                cursor.execute(
                    "INSERT INTO agendamento_servicos (agendamento_id, servico_id) VALUES (%s, %s)",
                    (agendamento_id, servico_id)
                )

            logger.info(f"Agendamento criado: ID {agendamento_id} para usuário {usuario_id}")

            return {
                "mensagem": "Agendamento realizado com sucesso",
                "agendamento_id": agendamento_id
            }

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato inválido. Use DD/MM/AAAA e HH:MM"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar agendamento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro ao processar agendamento"
        )


# 🔹 Visualizar agendamento específico (usando context manager)
@app.get("/agendamentos/{agendamento_id}", tags=["Agendamentos"])
def ver_agendamento(agendamento_id: int) -> List[Dict[str, Any]]:
    """Visualiza detalhes de um agendamento específico"""
    try:
        with get_db_cursor(dictionary=True) as cursor:
            query = """
            SELECT 
                u.id AS usuario_id,
                u.nome AS cliente,
                u.email,
                a.id AS agendamento_id,
                a.data_agendamento,
                a.hora_agendamento,
                s.id AS servico_id,
                s.nome AS servico,
                s.preco
            FROM agendamentos a
            JOIN usuarios u ON u.id = a.usuario_id
            JOIN agendamento_servicos ags ON ags.agendamento_id = a.id
            JOIN servicos s ON s.id = ags.servico_id
            WHERE a.id = %s
            ORDER BY s.id
            """

            cursor.execute(query, (agendamento_id,))
            resultado = cursor.fetchall()

            if not resultado:
                logger.warning(f"Agendamento {agendamento_id} não encontrado")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Agendamento não encontrado"
                )

            logger.info(f"Agendamento {agendamento_id} visualizado")
            return resultado

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao visualizar agendamento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao carregar agendamento"
        )


# 🔹 Listar todos agendamentos de um usuário (usando context manager)
@app.get("/usuarios/{email}/agendamentos", tags=["Agendamentos"])
def listar_agendamentos_usuario(email: EmailStr) -> List[Dict[str, Any]]:
    """Lista todos agendamentos de um usuário específico"""
    try:
        with get_db_cursor(dictionary=True) as cursor:
            query = """
            SELECT 
                a.id,
                a.data_agendamento,
                a.hora_agendamento,
                GROUP_CONCAT(s.nome SEPARATOR ', ') as servicos,
                COUNT(s.id) as quantidade_servicos,
                SUM(s.preco) as valor_total
            FROM agendamentos a
            JOIN usuarios u ON u.id = a.usuario_id
            LEFT JOIN agendamento_servicos ags ON ags.agendamento_id = a.id
            LEFT JOIN servicos s ON s.id = ags.servico_id
            WHERE u.email = %s
            GROUP BY a.id
            ORDER BY a.data_agendamento DESC, a.hora_agendamento DESC
            """

            cursor.execute(query, (email,))
            agendamentos = cursor.fetchall()

            if not agendamentos:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Nenhum agendamento encontrado para este usuário"
                )

            logger.info(f"Listados {len(agendamentos)} agendamentos para {email}")
            return agendamentos

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao listar agendamentos do usuário: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao carregar agendamentos"
        )