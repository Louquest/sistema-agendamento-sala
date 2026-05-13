from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from database import get_db_cursor, get_db_status, test_connection
from typing import List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator
import logging
import re

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Models Pydantic
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


class PrecoUpdateRequest(BaseModel):
    preco: float = Field(..., gt=0, description="Novo preço do serviço (maior que zero)")


app = FastAPI(
    title="API de Agendamentos",
    description="Sistema de gerenciamento de agendamentos e serviços",
    version="1.0.0"
)

# 🔹 Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def formatar_hora(hora):
    if not hora:
        return None
    if hasattr(hora, 'total_seconds'):
        total_seconds = int(hora.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"
    if isinstance(hora, str):
        match = re.search(r'PT(\d+)H(\d+)M', hora)
        if match:
            hours = match.group(1)
            minutes = match.group(2)
            return f"{int(hours):02d}:{int(minutes):02d}"
        if ':' in hora:
            parts = hora.split(':')
            if len(parts) >= 2:
                return f"{int(parts[0]):02d}:{int(parts[1]):02d}"
    return str(hora)[:5] if hora else None


# ============================================================
# ENDPOINTS BÁSICOS
# ============================================================

@app.get("/status", tags=["Sistema"])
def status_sistema() -> Dict[str, Any]:
    db_status = get_db_status()
    return {
        "api": "online",
        "database": db_status,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/", tags=["Home"])
def home() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/teste-banco", tags=["Sistema"])
def teste_banco() -> Dict[str, Any]:
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


@app.post("/usuarios", status_code=status.HTTP_201_CREATED, tags=["Usuários"])
def criar_usuario(usuario: UsuarioRequest) -> Dict[str, str]:
    try:
        with get_db_cursor(dictionary=False) as cursor:
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


@app.post("/login", tags=["Autenticação"])
def login(login_data: LoginRequest) -> Dict[str, Any]:
    try:
        with get_db_cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT id, nome, email, telefone, tipo FROM usuarios WHERE email = %s AND senha = %s",
                (login_data.email, login_data.senha)
            )
            usuario = cursor.fetchone()
            if not usuario:
                logger.warning(f"Tentativa de login inválida para: {login_data.email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Email ou senha inválidos"
                )
            logger.info(f"Login realizado: {login_data.email} - Tipo: {usuario['tipo']}")
            return {"mensagem": "Login realizado com sucesso", "usuario": usuario}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar login"
        )


@app.get("/servicos", response_model=List[ServicoResponse], tags=["Serviços"])
def listar_servicos() -> List[Dict[str, Any]]:
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


@app.post("/agendamentos", response_model=AgendamentoResponse, status_code=status.HTTP_201_CREATED,
          tags=["Agendamentos"])
def criar_agendamento(dados: AgendamentoRequest) -> Dict[str, Any]:
    try:
        with get_db_cursor(dictionary=False) as cursor:
            cursor.execute("SELECT id FROM usuarios WHERE email = %s", (dados.email,))
            usuario = cursor.fetchone()
            if not usuario:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuário não encontrado"
                )
            usuario_id = usuario[0]
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
            cursor.execute(
                "INSERT INTO agendamentos (usuario_id, data_agendamento, hora_agendamento) VALUES (%s, %s, %s)",
                (usuario_id, data_convertida, hora_convertida)
            )
            agendamento_id = cursor.lastrowid
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


@app.get("/usuarios/{email}/agendamentos", tags=["Agendamentos"])
def listar_agendamentos_usuario(email: EmailStr) -> List[Dict[str, Any]]:
    try:
        with get_db_cursor(dictionary=True) as cursor:
            query = """
            SELECT a.id, a.data_agendamento, a.hora_agendamento, a.status, a.criado_em
            FROM agendamentos a
            JOIN usuarios u ON u.id = a.usuario_id
            WHERE u.email = %s
            ORDER BY a.data_agendamento DESC, a.hora_agendamento DESC
            """
            cursor.execute(query, (email,))
            agendamentos = cursor.fetchall()
            if not agendamentos:
                return []
            for agendamento in agendamentos:
                agendamento['hora_agendamento'] = formatar_hora(agendamento['hora_agendamento'])
                if agendamento['data_agendamento']:
                    agendamento['data_agendamento'] = agendamento['data_agendamento'].strftime("%d/%m/%Y")
                if agendamento['criado_em']:
                    agendamento['criado_em'] = agendamento['criado_em'].strftime("%d/%m/%Y %H:%M")
                cursor.execute("""
                    SELECT s.nome, s.preco
                    FROM servicos s
                    JOIN agendamento_servicos ags ON ags.servico_id = s.id
                    WHERE ags.agendamento_id = %s
                """, (agendamento['id'],))
                servicos = cursor.fetchall()
                if servicos:
                    agendamento['servicos'] = ', '.join([s['nome'] for s in servicos])
                    agendamento['quantidade_servicos'] = len(servicos)
                    agendamento['valor_total'] = sum(float(s['preco']) for s in servicos)
                else:
                    agendamento['servicos'] = None
                    agendamento['quantidade_servicos'] = 0
                    agendamento['valor_total'] = None
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


@app.post("/admin/agendamentos/todos", tags=["Administração"])
def listar_todos_agendamentos(credenciais: LoginRequest) -> Dict[str, Any]:
    try:
        with get_db_cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT id, nome, tipo FROM usuarios WHERE email = %s AND senha = %s",
                (credenciais.email, credenciais.senha)
            )
            usuario = cursor.fetchone()
            if not usuario:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Credenciais inválidas"
                )
            if usuario['tipo'] not in ['admin', 'funcionario']:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Acesso negado. Apenas administradores e funcionários podem ver todos os agendamentos."
                )
            query = """
            SELECT 
                a.id AS agendamento_id,
                u.nome AS cliente_nome,
                u.email AS cliente_email,
                u.telefone AS cliente_telefone,
                a.data_agendamento,
                a.hora_agendamento,
                a.status,
                a.criado_em,
                GROUP_CONCAT(DISTINCT s.nome ORDER BY s.nome SEPARATOR ', ') AS servicos,
                COUNT(DISTINCT s.id) AS quantidade_servicos,
                SUM(s.preco) AS valor_total
            FROM agendamentos a
            INNER JOIN usuarios u ON u.id = a.usuario_id
            LEFT JOIN agendamento_servicos ags ON ags.agendamento_id = a.id
            LEFT JOIN servicos s ON s.id = ags.servico_id
            GROUP BY a.id, u.nome, u.email, u.telefone, a.data_agendamento, a.hora_agendamento, a.status, a.criado_em
            ORDER BY a.data_agendamento DESC, a.hora_agendamento DESC
            """
            cursor.execute(query)
            agendamentos = cursor.fetchall()
            for agendamento in agendamentos:
                if agendamento['hora_agendamento']:
                    agendamento['hora_agendamento'] = formatar_hora(agendamento['hora_agendamento'])
                if agendamento['valor_total']:
                    agendamento['valor_total'] = float(agendamento['valor_total'])
                else:
                    agendamento['valor_total'] = 0
                if agendamento['data_agendamento']:
                    agendamento['data_agendamento'] = agendamento['data_agendamento'].strftime("%d/%m/%Y")
                if agendamento['criado_em']:
                    agendamento['criado_em'] = agendamento['criado_em'].strftime("%d/%m/%Y %H:%M")
                if not agendamento['servicos']:
                    agendamento['servicos'] = "Nenhum serviço"
                    agendamento['quantidade_servicos'] = 0
            return {
                "status": "success",
                "total_agendamentos": len(agendamentos),
                "usuario_autenticado": {"nome": usuario['nome'], "tipo": usuario['tipo']},
                "agendamentos": agendamentos,
                "consultado_em": datetime.now().isoformat()
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao listar todos agendamentos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao carregar agendamentos: {str(e)}"
        )


@app.put("/agendamentos/{agendamento_id}/cancelar", tags=["Agendamentos"])
def cancelar_agendamento(agendamento_id: int, email: str = None, senha: str = None):
    try:
        with get_db_cursor(dictionary=True) as cursor:
            cursor.execute("""
                SELECT a.id, a.usuario_id, a.status, u.email, u.tipo, u.senha
                FROM agendamentos a
                JOIN usuarios u ON u.id = a.usuario_id
                WHERE a.id = %s
            """, (agendamento_id,))
            agendamento = cursor.fetchone()
            if not agendamento:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agendamento não encontrado")
            if agendamento['status'] == 'cancelado':
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agendamento já está cancelado")
            if agendamento['status'] == 'concluido':
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agendamento já foi concluído")
            is_admin = False
            if email and senha:
                cursor.execute("SELECT tipo FROM usuarios WHERE email = %s AND senha = %s", (email, senha))
                usuario_requisitante = cursor.fetchone()
                if usuario_requisitante and usuario_requisitante['tipo'] in ['admin', 'funcionario']:
                    is_admin = True
            if not is_admin:
                if not email:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="É necessário fornecer email")
                if email != agendamento['email']:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                        detail="Você só pode cancelar seus próprios agendamentos")
            cursor.execute("UPDATE agendamentos SET status = 'cancelado' WHERE id = %s", (agendamento_id,))
            logger.info(f"Agendamento {agendamento_id} cancelado por {email or 'admin'}")
            return {"mensagem": "Agendamento cancelado com sucesso", "agendamento_id": agendamento_id,
                    "status": "cancelado"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao cancelar agendamento: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Erro ao cancelar agendamento: {str(e)}")


@app.put("/servicos/{servico_id}/preco", tags=["Administração"])
def atualizar_preco_servico(servico_id: int, preco_request: PrecoUpdateRequest):
    try:
        with get_db_cursor(dictionary=False) as cursor:
            cursor.execute("SELECT id, nome, preco FROM servicos WHERE id = %s", (servico_id,))
            servico = cursor.fetchone()
            if not servico:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Serviço não encontrado")
            novo_preco = preco_request.preco
            if novo_preco < 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Preço não pode ser negativo")
            cursor.execute("UPDATE servicos SET preco = %s WHERE id = %s", (novo_preco, servico_id))
            return {"mensagem": "Preço atualizado com sucesso", "servico_id": servico_id, "novo_preco": novo_preco}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar preço: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Erro ao atualizar preço: {str(e)}")


@app.get("/agendamentos/horarios-disponiveis", tags=["Agendamentos"])
def horarios_disponiveis(data: str) -> Dict[str, Any]:
    try:
        data_convertida = datetime.strptime(data, "%d/%m/%Y").date()
        with get_db_cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT DISTINCT hora_agendamento FROM agendamentos WHERE data_agendamento = %s AND status = 'agendado' ORDER BY hora_agendamento",
                (data_convertida,))
            ocupados = cursor.fetchall()
            horarios_ocupados = [formatar_hora(h['hora_agendamento']) for h in ocupados if h['hora_agendamento']]
            todos_horarios = ["08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30",
                              "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00", "17:30",
                              "18:00", "18:30", "19:00", "19:30", "20:00"]
            horarios_disponiveis = [h for h in todos_horarios if h not in horarios_ocupados]
            return {"status": "success", "data": data, "horarios_ocupados": horarios_ocupados,
                    "horarios_disponiveis": horarios_disponiveis}
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato inválido. Use DD/MM/AAAA")
    except Exception as e:
        logger.error(f"Erro ao verificar disponibilidade: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Erro ao verificar horários disponíveis")


@app.put("/agendamentos/{agendamento_id}/concluir", tags=["Administração"])
def concluir_agendamento(agendamento_id: int, email: str = None, senha: str = None):
    try:
        with get_db_cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT a.id, a.usuario_id, a.status, u.email, u.tipo FROM agendamentos a JOIN usuarios u ON u.id = a.usuario_id WHERE a.id = %s",
                (agendamento_id,))
            agendamento = cursor.fetchone()
            if not agendamento:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agendamento não encontrado")
            if agendamento['status'] == 'concluido':
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agendamento já está concluído")
            if email and senha:
                cursor.execute("SELECT tipo FROM usuarios WHERE email = %s AND senha = %s", (email, senha))
                usuario_requisitante = cursor.fetchone()
                if not usuario_requisitante or usuario_requisitante['tipo'] not in ['admin', 'funcionario']:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                        detail="Apenas administradores podem concluir agendamentos")
            else:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                    detail="É necessário fornecer credenciais")
            cursor.execute("UPDATE agendamentos SET status = 'concluido' WHERE id = %s", (agendamento_id,))
            return {"mensagem": "Agendamento concluído com sucesso", "agendamento_id": agendamento_id,
                    "status": "concluido"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao concluir agendamento: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Erro ao concluir agendamento: {str(e)}")


@app.delete("/agendamentos/{agendamento_id}", tags=["Administração"])
def deletar_agendamento(agendamento_id: int, email: str = None, senha: str = None):
    try:
        with get_db_cursor(dictionary=True) as cursor:
            cursor.execute("SELECT a.id FROM agendamentos a WHERE a.id = %s", (agendamento_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agendamento não encontrado")
            if email and senha:
                cursor.execute("SELECT tipo FROM usuarios WHERE email = %s AND senha = %s", (email, senha))
                usuario_requisitante = cursor.fetchone()
                if not usuario_requisitante or usuario_requisitante['tipo'] not in ['admin', 'funcionario']:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                        detail="Apenas administradores podem deletar agendamentos")
            else:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                    detail="É necessário fornecer credenciais")
            cursor.execute("DELETE FROM agendamento_servicos WHERE agendamento_id = %s", (agendamento_id,))
            cursor.execute("DELETE FROM agendamentos WHERE id = %s", (agendamento_id,))
            return {"mensagem": "Agendamento deletado com sucesso", "agendamento_id": agendamento_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao deletar agendamento: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Erro ao deletar agendamento: {str(e)}")


# ============================================================
# ENDPOINTS PARA GERENCIAR CLIENTES
# ============================================================

@app.get("/admin/usuarios", tags=["Administração"])
def listar_usuarios_admin(email: str = None, senha: str = None):
    try:
        with get_db_cursor(dictionary=True) as cursor:
            if email and senha:
                cursor.execute("SELECT tipo FROM usuarios WHERE email = %s AND senha = %s", (email, senha))
                usuario_requisitante = cursor.fetchone()
                if not usuario_requisitante or usuario_requisitante['tipo'] not in ['admin', 'funcionario']:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
            else:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais necessárias")
            cursor.execute("SELECT id, nome, email, telefone, tipo, criado_em FROM usuarios ORDER BY id")
            usuarios = cursor.fetchall()
            for usuario in usuarios:
                if usuario['criado_em']:
                    usuario['criado_em'] = usuario['criado_em'].strftime("%d/%m/%Y %H:%M")
            return {"status": "success", "total": len(usuarios), "usuarios": usuarios}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao listar usuários: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Erro ao listar usuários: {str(e)}")


@app.put("/admin/usuarios/{usuario_id}", tags=["Administração"])
def editar_usuario(
        usuario_id: int,
        nome: str = None,
        email: str = None,
        telefone: str = None,
        tipo: str = None,
        admin_email: str = None,
        admin_senha: str = None
):
    try:
        with get_db_cursor(dictionary=True) as cursor:
            if admin_email and admin_senha:
                cursor.execute("SELECT tipo FROM usuarios WHERE email = %s AND senha = %s", (admin_email, admin_senha))
                usuario_requisitante = cursor.fetchone()
                if not usuario_requisitante or usuario_requisitante['tipo'] not in ['admin', 'funcionario']:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
            else:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais necessárias")
            cursor.execute("SELECT id FROM usuarios WHERE id = %s", (usuario_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
            updates = []
            params = []
            if nome:
                updates.append("nome = %s")
                params.append(nome)
            if email:
                updates.append("email = %s")
                params.append(email)
            if telefone:
                updates.append("telefone = %s")
                params.append(telefone)
            if tipo and tipo in ['cliente', 'funcionario', 'admin']:
                updates.append("tipo = %s")
                params.append(tipo)
            if not updates:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nenhum campo para atualizar")
            params.append(usuario_id)
            query = f"UPDATE usuarios SET {', '.join(updates)} WHERE id = %s"
            cursor.execute(query, params)
            return {"mensagem": "Usuário atualizado com sucesso", "usuario_id": usuario_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao editar usuário: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Erro ao editar usuário: {str(e)}")


@app.put("/admin/usuarios/{usuario_id}/reset-senha", tags=["Administração"])
def resetar_senha_usuario(
        usuario_id: int,
        nova_senha: str = None,
        admin_email: str = None,
        admin_senha: str = None
):
    """
    Reseta a senha de um usuário (apenas admin/funcionario)
    OBRIGATÓRIO: enviar nova_senha (não gera senha automática)
    """
    try:
        with get_db_cursor(dictionary=True) as cursor:
            # Verificar permissão
            if admin_email and admin_senha:
                cursor.execute(
                    "SELECT tipo FROM usuarios WHERE email = %s AND senha = %s",
                    (admin_email, admin_senha)
                )
                usuario_requisitante = cursor.fetchone()
                if not usuario_requisitante or usuario_requisitante['tipo'] not in ['admin', 'funcionario']:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Acesso negado. Apenas administradores e funcionários podem resetar senhas"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="É necessário fornecer credenciais de administrador"
                )

            # Verificar se o usuário existe
            cursor.execute("SELECT id, nome FROM usuarios WHERE id = %s", (usuario_id,))
            usuario = cursor.fetchone()
            if not usuario:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuário não encontrado"
                )

            # VALIDAÇÃO: nova_senha é OBRIGATÓRIA (NÃO GERAR AUTOMÁTICA!)
            if not nova_senha:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="É obrigatório informar a nova senha"
                )

            # Validar tamanho mínimo
            if len(nova_senha) < 6:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A nova senha deve ter pelo menos 6 caracteres"
                )

            # Atualizar senha
            cursor.execute(
                "UPDATE usuarios SET senha = %s WHERE id = %s",
                (nova_senha, usuario_id)
            )

            logger.info(f"Senha do usuário {usuario_id} ({usuario['nome']}) alterada por {admin_email}")

            return {
                "mensagem": "Senha alterada com sucesso",
                "usuario_id": usuario_id,
                "usuario_nome": usuario['nome']
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao resetar senha: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao resetar senha: {str(e)}"
        )


@app.delete("/admin/usuarios/{usuario_id}", tags=["Administração"])
def deletar_usuario(usuario_id: int, admin_email: str = None, admin_senha: str = None):
    try:
        with get_db_cursor(dictionary=True) as cursor:
            if admin_email and admin_senha:
                cursor.execute("SELECT tipo, id FROM usuarios WHERE email = %s AND senha = %s",
                               (admin_email, admin_senha))
                admin_data = cursor.fetchone()
                if not admin_data or admin_data['tipo'] != 'admin':
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                        detail="Apenas administradores podem deletar usuários")
                if admin_data['id'] == usuario_id:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                        detail="Você não pode deletar sua própria conta")
            else:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais necessárias")
            cursor.execute("SELECT id, nome FROM usuarios WHERE id = %s", (usuario_id,))
            usuario = cursor.fetchone()
            if not usuario:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
            cursor.execute("SELECT id FROM agendamentos WHERE usuario_id = %s", (usuario_id,))
            agendamentos = cursor.fetchall()
            for ag in agendamentos:
                cursor.execute("DELETE FROM agendamento_servicos WHERE agendamento_id = %s", (ag['id'],))
            cursor.execute("DELETE FROM agendamentos WHERE usuario_id = %s", (usuario_id,))
            cursor.execute("DELETE FROM usuarios WHERE id = %s", (usuario_id,))
            return {"mensagem": "Usuário deletado com sucesso", "usuario_id": usuario_id,
                    "usuario_nome": usuario['nome']}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao deletar usuário: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Erro ao deletar usuário: {str(e)}")


# ============================================================
# ENDPOINTS PARA BANNER PROMOCIONAL
# ============================================================

# Variavel para armazenar o banner (em producao, salvar no banco)
banner_promocional = "PROMOCAO ESPECIAL<br>Corte + Escova por apenas R$ 89,90!<br><small>Valido para agendamentos ate 30/06</small>"


@app.get("/admin/banner", tags=["Administracao"])
def get_banner():
    """Retorna o banner promocional atual"""
    return {"banner": banner_promocional}


@app.put("/admin/banner", tags=["Administracao"])
def update_banner(banner: str, admin_email: str = None, admin_senha: str = None):
    """Atualiza o banner promocional (apenas admin)"""
    global banner_promocional
    try:
        # Verificar permissao
        if admin_email and admin_senha:
            with get_db_cursor(dictionary=True) as cursor:
                cursor.execute("SELECT tipo FROM usuarios WHERE email = %s AND senha = %s", (admin_email, admin_senha))
                usuario = cursor.fetchone()
                if not usuario or usuario['tipo'] not in ['admin', 'funcionario']:
                    raise HTTPException(status_code=403, detail="Acesso negado")
        else:
            raise HTTPException(status_code=401, detail="Credenciais necessarias")

        banner_promocional = banner
        logger.info(f"Banner atualizado por {admin_email}")
        return {"mensagem": "Banner atualizado com sucesso", "banner": banner_promocional}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar banner: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar banner: {str(e)}")


# ============================================================
# EXECUÇÃO
# ============================================================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)