// api.js - Configuração da API
const API_BASE_URL = "http://localhost:8000";

// Função genérica para requisições
async function apiRequest(endpoint, method = "GET", body = null) {
    const options = {
        method: method,
        headers: {
            "Content-Type": "application/json",
        },
    };
    if (body) {
        options.body = JSON.stringify(body);
    }
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
    const data = await response.json();
    
    if (!response.ok) {
        throw { status: response.status, detail: data.detail || "Erro na requisição" };
    }
    return data;
}

// Funções específicas
async function cadastrarUsuario(nome, email, senha, telefone) {
    return apiRequest("/usuarios", "POST", { nome, email, senha, telefone });
}

// FUNÇÃO LOGIN CORRIGIDA - Salva a senha no localStorage
async function login(email, senha) {
    const data = await apiRequest("/login", "POST", { email, senha });
    const usuarioCompleto = {
        ...data.usuario,
        senha: senha
    };
    localStorage.setItem("usuario", JSON.stringify(usuarioCompleto));
    return data;
}

async function listarServicos() {
    return apiRequest("/servicos", "GET");
}

async function criarAgendamento(email, data, hora, servicosIds) {
    return apiRequest("/agendamentos", "POST", { email, data, hora, servicos: servicosIds });
}

async function listarMeusAgendamentos(email) {
    return apiRequest(`/usuarios/${encodeURIComponent(email)}/agendamentos`, "GET");
}

async function horariosDisponiveis(data) {
    return apiRequest(`/agendamentos/horarios-disponiveis?data=${data}`, "GET");
}

// Cancelar agendamento
async function cancelarAgendamento(agendamentoId, email, senha) {
    const url = `${API_BASE_URL}/agendamentos/${agendamentoId}/cancelar?email=${encodeURIComponent(email)}&senha=${encodeURIComponent(senha)}`;
    console.log("Cancelando agendamento:", url);
    
    const response = await fetch(url, {
        method: "PUT",
        headers: { "Content-Type": "application/json" }
    });
    const data = await response.json();
    if (!response.ok) {
        throw { status: response.status, detail: data.detail || "Erro ao cancelar" };
    }
    return data;
}

// ============================================================
// FUNCOES PARA ADMIN GERENCIAR CLIENTES
// ============================================================

// Listar todos usuarios (admin/funcionario)
async function listarTodosUsuarios(email, senha) {
    const url = `${API_BASE_URL}/admin/usuarios?email=${encodeURIComponent(email)}&senha=${encodeURIComponent(senha)}`;
    const response = await fetch(url);
    const data = await response.json();
    if (!response.ok) {
        throw { status: response.status, detail: data.detail };
    }
    return data;
}

// Editar usuario
async function editarUsuario(usuarioId, dados, adminEmail, adminSenha) {
    const params = new URLSearchParams();
    params.append('admin_email', adminEmail);
    params.append('admin_senha', adminSenha);
    
    if (dados.nome) params.append('nome', dados.nome);
    if (dados.email) params.append('email', dados.email);
    if (dados.telefone) params.append('telefone', dados.telefone);
    if (dados.tipo) params.append('tipo', dados.tipo);
    
    const response = await fetch(`${API_BASE_URL}/admin/usuarios/${usuarioId}?${params.toString()}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" }
    });
    const data = await response.json();
    if (!response.ok) {
        throw { status: response.status, detail: data.detail };
    }
    return data;
}

// Resetar senha do usuario
async function resetarSenhaUsuario(usuarioId, adminEmail, adminSenha, novaSenha = null) {
    let url = `${API_BASE_URL}/admin/usuarios/${usuarioId}/reset-senha?admin_email=${encodeURIComponent(adminEmail)}&admin_senha=${encodeURIComponent(adminSenha)}`;
    if (novaSenha) {
        url += `&nova_senha=${encodeURIComponent(novaSenha)}`;
    }
    const response = await fetch(url, { method: "PUT" });
    const data = await response.json();
    if (!response.ok) {
        throw { status: response.status, detail: data.detail };
    }
    return data;
}

// Deletar usuario (apenas admin)
async function deletarUsuario(usuarioId, adminEmail, adminSenha) {
    const url = `${API_BASE_URL}/admin/usuarios/${usuarioId}?admin_email=${encodeURIComponent(adminEmail)}&admin_senha=${encodeURIComponent(adminSenha)}`;
    const response = await fetch(url, { method: "DELETE" });
    const data = await response.json();
    if (!response.ok) {
        throw { status: response.status, detail: data.detail };
    }
    return data;
}

// ============================================================
// FUNCOES PARA BANNER PROMOCIONAL
// ============================================================

// Buscar banner promocional
async function getBanner() {
    const response = await fetch(`${API_BASE_URL}/admin/banner`);
    const data = await response.json();
    return data;
}

// Atualizar banner promocional (admin)
async function updateBanner(banner, adminEmail, adminSenha) {
    const url = `${API_BASE_URL}/admin/banner?admin_email=${encodeURIComponent(adminEmail)}&admin_senha=${encodeURIComponent(adminSenha)}&banner=${encodeURIComponent(banner)}`;
    const response = await fetch(url, { method: "PUT" });
    const data = await response.json();
    if (!response.ok) {
        throw { status: response.status, detail: data.detail };
    }
    return data;
}