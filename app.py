from flask import Flask, render_template, request, redirect, send_from_directory, url_for, session, flash, jsonify
import sqlite3
import hashlib
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

import sqlite3

# Limpar todos os bancos de dados
def limpar_bancos():
    # Banco de login
    conn_login = sqlite3.connect('login.db')
    cursor_login = conn_login.cursor()
    cursor_login.execute("DELETE FROM usuarios")
    cursor_login.execute("DELETE FROM sqlite_sequence WHERE name='usuarios'")
    conn_login.commit()
    conn_login.close()
    
    # Banco de perfil
    conn_perfil = sqlite3.connect('perfil.db')
    cursor_perfil = conn_perfil.cursor()
    cursor_perfil.execute("DELETE FROM perfis")
    cursor_perfil.execute("DELETE FROM sqlite_sequence WHERE name='perfis'")
    conn_perfil.commit()
    conn_perfil.close()
    
    # Banco de posts
    conn_posts = sqlite3.connect('posts.db')
    cursor_posts = conn_posts.cursor()
    cursor_posts.execute("DELETE FROM comentarios")
    cursor_posts.execute("DELETE FROM posts")
    cursor_posts.execute("DELETE FROM sqlite_sequence WHERE name IN ('posts', 'comentarios')")
    conn_posts.commit()
    conn_posts.close()
    
    print("Todos os bancos de dados foram limpos!")

# Executar limpeza
limpar_bancos()

# Configurações
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}

# Função para verificar extensões de arquivo permitidas
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Função para criar as tabelas no banco de dados (SIMPLIFICADA)
def init_db():
    # Conexão com o banco de login (existente)
    conn_login = sqlite3.connect('login.db')
    cursor_login = conn_login.cursor()
    cursor_login.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    ''')
    conn_login.commit()
    conn_login.close()
    
    # Conexão com o banco de perfil (existente)
    conn_perfil = sqlite3.connect('perfil.db')
    cursor_perfil = conn_perfil.cursor()
    cursor_perfil.execute('''
        CREATE TABLE IF NOT EXISTS perfis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER UNIQUE,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            escolaridade TEXT,
            nome_completo TEXT,
            data_nascimento TEXT,
            avatar TEXT,
            profissao TEXT,
            endereco TEXT,
            contato TEXT,
            descricao TEXT,
            formacao TEXT,
            experiencia TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')
    conn_perfil.commit()
    conn_perfil.close()
    
    # Conexão com o banco de postagens (atualizada com comentários)
    conn_posts = sqlite3.connect('posts.db')
    cursor_posts = conn_posts.cursor()
    
    # Tabela de posts (existente)
    cursor_posts.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            titulo TEXT NOT NULL,
            conteudo TEXT,
            categoria TEXT NOT NULL,
            arquivo TEXT,
            tags TEXT,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            votos INTEGER DEFAULT 0
        )
    ''')
    
    # Tabela de comentários (nova)
    cursor_posts.execute('''
        CREATE TABLE IF NOT EXISTS comentarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            usuario_id INTEGER NOT NULL,
            texto TEXT NOT NULL,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE
        )
    ''')
    
    conn_posts.commit()
    conn_posts.close()
    
    print("Banco de dados inicializado com sucesso!")

# Função para hash de senha
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

# Função para obter dados do perfil
def obter_perfil(usuario_id):
    conn = sqlite3.connect('perfil.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM perfis WHERE usuario_id = ?', (usuario_id,))
    perfil = cursor.fetchone()
    conn.close()
    
    if perfil:
        return {
            'id': perfil[0],
            'usuario_id': perfil[1],
            'username': perfil[2] if perfil[2] else 'Usuário',
            'email': perfil[3] if perfil[3] else '',
            'escolaridade': perfil[4] if len(perfil) > 4 and perfil[4] else '',
            'nome_completo': perfil[5] if len(perfil) > 5 and perfil[5] else '',
            'data_nascimento': perfil[6] if len(perfil) > 6 and perfil[6] else '',
            'avatar': perfil[7] if len(perfil) > 7 and perfil[7] else '👤',
            'profissao': perfil[8] if len(perfil) > 8 and perfil[8] else 'Profissão não informada',
            'endereco': perfil[9] if len(perfil) > 9 and perfil[9] else 'Endereço não informado',
            'contato': perfil[10] if len(perfil) > 10 and perfil[10] else 'Telefone não informado',
            'descricao': perfil[11] if len(perfil) > 11 and perfil[11] else 'Descrição não informada',
            'formacao': perfil[12] if len(perfil) > 12 and perfil[12] else 'Formação não informada',
            'experiencia': perfil[13] if len(perfil) > 13 and perfil[13] else 'Experiência não informada'
        }
    return None

# Função para obter username do perfil
def obter_username(usuario_id):
    conn = sqlite3.connect('perfil.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM perfis WHERE usuario_id = ?', (usuario_id,))
    resultado = cursor.fetchone()
    conn.close()
    
    if resultado and resultado[0]:
        return resultado[0]
    return f"Usuário_{usuario_id}"

# Função para formatar data (reutilizável)
def formatar_data(data_criacao):
    data_formatada = "Data não disponível"
    if data_criacao:
        try:
            if isinstance(data_criacao, str):
                if 'T' in data_criacao:
                    data_obj = datetime.fromisoformat(data_criacao.replace('Z', ''))
                else:
                    try:
                        data_obj = datetime.strptime(data_criacao, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        data_obj = datetime.strptime(data_criacao, '%Y-%m-%d %H:%M')
                data_formatada = data_obj.strftime('%d/%m/%Y %H:%M')
            else:
                data_formatada = data_criacao.strftime('%d/%m/%Y %H:%M')
        except (ValueError, AttributeError) as e:
            print(f"Erro ao formatar data {data_criacao}: {e}")
            data_formatada = str(data_criacao)[:16].replace('T', ' ')
    return data_formatada

# Função para obter posts do banco de dados (SISTEMA SIMPLIFICADO)
def obter_posts(categoria=None, ordenar_por_votos=False):
    conn = sqlite3.connect('posts.db')
    cursor = conn.cursor()
    
    try:
        if categoria and categoria != 'todos':
            if ordenar_por_votos:
                cursor.execute('''
                    SELECT * FROM posts 
                    WHERE categoria = ? 
                    ORDER BY votos DESC, data_criacao DESC
                ''', (categoria,))
            else:
                cursor.execute('''
                    SELECT * FROM posts 
                    WHERE categoria = ? 
                    ORDER BY data_criacao DESC
                ''', (categoria,))
        else:
            if ordenar_por_votos:
                cursor.execute('SELECT * FROM posts ORDER BY votos DESC, data_criacao DESC')
            else:
                cursor.execute('SELECT * FROM posts ORDER BY data_criacao DESC')
        
        posts = cursor.fetchall()
        
    except sqlite3.Error as e:
        print(f"Erro no banco de dados: {e}")
        posts = []
    
    conn.close()
    
    posts_formatados = []
    for post in posts:
        if len(post) >= 9:
            data_formatada = formatar_data(post[7])
            
            posts_formatados.append({
                'id': post[0],
                'username': post[1],
                'titulo': post[2],
                'conteudo': post[3],
                'categoria': post[4],
                'arquivo': post[5],
                'tags': post[6],
                'data_criacao': data_formatada,
                'votos': post[8],
                'autor_username': post[1],
                'data_original': post[7]
            })
    
    return posts_formatados

# Função para atualizar votos (SISTEMA SIMPLIFICADO)
def atualizar_votos(post_id, tipo_voto):
    conn = sqlite3.connect('posts.db')
    cursor = conn.cursor()
    
    try:
        # Apenas incrementa ou decrementa a contagem total de votos
        if tipo_voto == 1:
            cursor.execute('UPDATE posts SET votos = votos + 1 WHERE id = ?', (post_id,))
        elif tipo_voto == -1:
            cursor.execute('UPDATE posts SET votos = votos - 1 WHERE id = ?', (post_id,))
        
        cursor.execute('SELECT votos FROM posts WHERE id = ?', (post_id,))
        novo_total_votos = cursor.fetchone()[0]
        
        conn.commit()
        return {'success': True, 'novo_total_votos': novo_total_votos}
        
    except sqlite3.Error as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()

# Função para criar um novo post
def criar_post(username, titulo, conteudo, categoria, arquivo, tags):
    conn = sqlite3.connect('posts.db')
    cursor = conn.cursor()
    
    data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('''
        INSERT INTO posts (username, titulo, conteudo, categoria, arquivo, tags, data_criacao)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (username, titulo, conteudo, categoria, arquivo, tags, data_atual))
    
    conn.commit()
    post_id = cursor.lastrowid
    conn.close()
    return post_id

# Função para migrar dados antigos
def migrar_dados_antigos():
    """Migra posts antigos (com usuario_id) para a nova estrutura (com username)"""
    conn_posts = sqlite3.connect('posts.db')
    cursor_posts = conn_posts.cursor()
    
    try:
        cursor_posts.execute("PRAGMA table_info(posts)")
        colunas = [coluna[1] for coluna in cursor_posts.fetchall()]
        
        if 'usuario_id' in colunas and 'username' not in colunas:
            print("Migrando dados antigos...")
            
            cursor_posts.execute('SELECT * FROM posts')
            posts_antigos = cursor_posts.fetchall()
            
            cursor_posts.execute('''
                CREATE TABLE posts_nova (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    titulo TEXT NOT NULL,
                    conteudo TEXT,
                    categoria TEXT NOT NULL,
                    arquivo TEXT,
                    tags TEXT,
                    data_criacao TIMESTAMP,
                    votos INTEGER DEFAULT 0
                )
            ''')
            
            for post in posts_antigos:
                usuario_id = post[1] if len(post) > 1 else None
                username = obter_username(usuario_id) if usuario_id else "Usuário_Desconhecido"
                
                cursor_posts.execute('''
                    INSERT INTO posts_nova (id, username, titulo, conteudo, categoria, arquivo, tags, data_criacao, votos)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (post[0], username, post[2], post[3], post[4], post[5], post[6], post[7], post[8] if len(post) > 8 else 0))
            
            cursor_posts.execute('DROP TABLE posts')
            cursor_posts.execute('ALTER TABLE posts_nova RENAME TO posts')
            conn_posts.commit()
            print("Migração concluída com sucesso!")
            
    except sqlite3.Error as e:
        print(f"Erro na migração: {e}")
    finally:
        conn_posts.close()

# Função para atualizar a estrutura da tabela
def atualizar_estrutura_tabela():
    conn = sqlite3.connect('perfil.db')
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(perfis)")
    colunas_existentes = [coluna[1] for coluna in cursor.fetchall()]
    
    colunas_necessarias = [
        'profissao', 'endereco', 'contato', 'descricao', 'formacao', 'experiencia'
    ]
    
    for coluna in colunas_necessarias:
        if coluna not in colunas_existentes:
            try:
                cursor.execute(f"ALTER TABLE perfis ADD COLUMN {coluna} TEXT")
                print(f"Coluna {coluna} adicionada com sucesso.")
            except sqlite3.Error as e:
                print(f"Erro ao adicionar coluna {coluna}: {e}")
    
    conn.commit()
    conn.close()

# Função para garantir que todos os perfis tenham username
def garantir_usernames():
    conn_perfil = sqlite3.connect('perfil.db')
    cursor_perfil = conn_perfil.cursor()
    
    cursor_perfil.execute("SELECT usuario_id, email FROM perfis WHERE username IS NULL OR username = ''")
    perfis_sem_username = cursor_perfil.fetchall()
    
    for perfil in perfis_sem_username:
        usuario_id, email = perfil
        username_padrao = email.split('@')[0] if email else f"Usuario_{usuario_id}"
        
        cursor_perfil.execute(
            "UPDATE perfis SET username = ? WHERE usuario_id = ?",
            (username_padrao, usuario_id)
        )
        print(f"Username definido para usuário {usuario_id}: {username_padrao}")
    
    conn_perfil.commit()
    conn_perfil.close()

# Função para corrigir datas existentes no banco
def corrigir_datas_existentes():
    """Corrige o formato das datas existentes no banco"""
    conn = sqlite3.connect('posts.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT id, data_criacao FROM posts')
        posts = cursor.fetchall()
        
        for post in posts:
            post_id, data_original = post
            if data_original and isinstance(data_original, str):
                try:
                    if 'T' in data_original:
                        data_obj = datetime.fromisoformat(data_original.replace('Z', ''))
                        data_corrigida = data_obj.strftime('%Y-%m-%d %H:%M:%S')
                        
                        cursor.execute(
                            'UPDATE posts SET data_criacao = ? WHERE id = ?',
                            (data_corrigida, post_id)
                        )
                        print(f"Data corrigida para post {post_id}: {data_original} -> {data_corrigida}")
                except ValueError as e:
                    print(f"Erro ao corrigir data do post {post_id}: {e}")
        
        conn.commit()
        print("Correção de datas concluída!")
        
    except sqlite3.Error as e:
        print(f"Erro ao corrigir datas: {e}")
    finally:
        conn.close()

# ========== ROTAS ==========

@app.route('/')
def index():
    if 'usuario_id' in session:
        perfil = obter_perfil(session['usuario_id'])
        return render_template('index.html', user=perfil)
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['user']
        senha = request.form['pass']
        senha_hash = hash_senha(senha)
        
        conn = sqlite3.connect('login.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM usuarios WHERE email = ? AND senha = ?', (email, senha_hash))
        usuario = cursor.fetchone()
        conn.close()
        
        if usuario:
            session['usuario_id'] = usuario[0]
            session['email'] = usuario[1]

            perfil = obter_perfil(usuario[0])
            if not perfil:
                conn_perfil = sqlite3.connect('perfil.db')
                cursor_perfil = conn_perfil.cursor()
                username_padrao = email.split('@')[0]
                cursor_perfil.execute(
                    'INSERT INTO perfis (usuario_id, username, email, profissao) VALUES (?, ?, ?, ?)',
                    (usuario[0], username_padrao, email, 'Profissão não informada')
                )
                conn_perfil.commit()
                conn_perfil.close()
            else:
                if not perfil['username'] or perfil['username'] == 'Usuário':
                    conn_perfil = sqlite3.connect('perfil.db')
                    cursor_perfil = conn_perfil.cursor()
                    username_padrao = email.split('@')[0]
                    cursor_perfil.execute(
                        'UPDATE perfis SET username = ? WHERE usuario_id = ?',
                        (username_padrao, usuario[0])
                    )
                    conn_perfil.commit()
                    conn_perfil.close()

            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Email ou senha incorretos!', 'danger')
    
    return render_template('login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        confirmar_email = request.form['confirm-email']
        senha = request.form['password']
        confirmar_senha = request.form['confirm-password']
        escolaridade = request.form['escolaridade']
        
        if email != confirmar_email:
            flash('Os emails não coincidem!', 'danger')
            return render_template('cadastro.html')
        
        if senha != confirmar_senha:
            flash('As senhas não coincidem!', 'danger')
            return render_template('cadastro.html')
        
        senha_hash = hash_senha(senha)
        
        try:
            conn_login = sqlite3.connect('login.db')
            cursor_login = conn_login.cursor()
            cursor_login.execute('INSERT INTO usuarios (email, senha) VALUES (?, ?)', (email, senha_hash))
            usuario_id = cursor_login.lastrowid
            conn_login.commit()
            conn_login.close()
            
            conn_perfil = sqlite3.connect('perfil.db')
            cursor_perfil = conn_perfil.cursor()
            cursor_perfil.execute('INSERT INTO perfis (usuario_id, username, email, escolaridade) VALUES (?, ?, ?, ?)', 
                                 (usuario_id, username, email, escolaridade))
            conn_perfil.commit()
            conn_perfil.close()
            
            session['usuario_id'] = usuario_id
            session['email'] = email
            
            flash('Cadastro realizado com sucesso!', 'success')
            return redirect(url_for('index'))
            
        except sqlite3.IntegrityError:
            flash('Este email já está cadastrado!', 'danger')
    
    return render_template('cadastro.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('index'))

@app.route('/perfil')
def perfil():
    if 'usuario_id' not in session:
        flash('Faça login para acessar esta página.', 'warning')
        return redirect(url_for('login'))
    
    perfil = obter_perfil(session['usuario_id'])
    return render_template('perfil/perfil.html', user=perfil)

@app.route('/EditarPerfil', methods=['GET', 'POST'])
def editar_perfil():
    if 'usuario_id' not in session:
        flash('Faça login para acessar esta página.', 'warning')
        return redirect(url_for('login'))
    
    perfil = obter_perfil(session['usuario_id'])
    
    if request.method == 'POST':
        username = request.form.get('username', '')
        profissao = request.form.get('profissao', '')
        endereco = request.form.get('endereco', '')
        contato = request.form.get('contato', '')
        descricao = request.form.get('descricao', '')
        formacao = request.form.get('formacao', '')
        experiencia = request.form.get('experiencia', '')
        nome_completo = request.form.get('nome_completo', '')
        data_nascimento = request.form.get('data_nascimento', '')
        escolaridade = request.form.get('escolaridade', '')
        
        if contato:
            contato_limpo = ''.join(filter(str.isdigit, contato))
            if len(contato_limpo) not in [10, 11]:
                flash('Telefone inválido. Deve ter 10 ou 11 dígitos.', 'danger')
                return render_template('perfil/EditarPerfil.html', user=perfil)
        
        try:
            conn = sqlite3.connect('perfil.db')
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE perfis 
                SET username = ?, profissao = ?, endereco = ?, contato = ?, 
                    descricao = ?, formacao = ?, experiencia = ?, nome_completo = ?, 
                    data_nascimento = ?, escolaridade = ?
                WHERE usuario_id = ?
            ''', (username, profissao, endereco, contato, descricao, formacao, 
                  experiencia, nome_completo, data_nascimento, escolaridade, 
                  session['usuario_id']))
            conn.commit()
            conn.close()
            
            flash('Perfil atualizado com sucesso!', 'success')
            return redirect(url_for('perfil'))
            
        except Exception as e:
            flash(f'Erro ao atualizar perfil: {str(e)}', 'danger')
    
    return render_template('perfil/EditarPerfil.html', user=perfil)

@app.route('/criar_post', methods=['POST'])
def criar_post_route():
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'Faça login para criar uma postagem.'})
    
    try:
        titulo = request.form.get('titulo')
        conteudo = request.form.get('conteudo')
        categoria = request.form.get('categoria')
        tags = request.form.get('tags', '')

        perfil = obter_perfil(session['usuario_id'])
        username = perfil['username'] if perfil and perfil['username'] else f"Usuario_{session['usuario_id']}"

        arquivo = None
        if 'arquivo' in request.files:
            file = request.files['arquivo']
            if file.filename != '' and allowed_file(file.filename):
                if not os.path.exists(UPLOAD_FOLDER):
                    os.makedirs(UPLOAD_FOLDER)
                
                filename = f"post_{session['usuario_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                arquivo = filename
        
        post_id = criar_post(username, titulo, conteudo, categoria, arquivo, tags)
        
        flash('Postagem criada com sucesso!', 'success')
        return redirect(url_for('pagina_tcc'))
    
    except Exception as e:
        flash(f'Erro ao criar postagem: {str(e)}', 'danger')
        return redirect(url_for('postagens_academicas'))

@app.route('/pagtcc')
def pagina_tcc():
    if 'usuario_id' not in session:
        flash('Faça login para acessar esta página.', 'warning')
        return redirect(url_for('login'))
    
    perfil = obter_perfil(session['usuario_id'])
    categoria = request.args.get('categoria', 'todos')
    ordenar_por_votos = request.args.get('ordenar', 'data') == 'votos'
    
    # Obter posts (sistema simplificado sem controle de votos individuais)
    posts_filtrados = obter_posts(
        categoria if categoria != 'todos' else None, 
        ordenar_por_votos
    )
    
    # Contagens
    todos_posts_para_contagem = obter_posts()
    contagens = {
        'todos': len(todos_posts_para_contagem),
        'TCC': len([p for p in todos_posts_para_contagem if p['categoria'] == 'TCC']),
        'IC': len([p for p in todos_posts_para_contagem if p['categoria'] == 'IC']),
        'Mestrado': len([p for p in todos_posts_para_contagem if p['categoria'] == 'Mestrado']),
        'Doutorado': len([p for p in todos_posts_para_contagem if p['categoria'] == 'Doutorado'])
    }
    
    return render_template('pagtcc.html', 
                         user=perfil, 
                         posts=posts_filtrados, 
                         categoria_selecionada=categoria,
                         contagens=contagens,
                         ordenar_por_votos=ordenar_por_votos)

@app.route('/atualizar_votos', methods=['POST'])
def atualizar_votos_route():
    """Rota simplificada para atualizar votos (sem controle por usuário)"""
    try:
        post_id = request.json.get('post_id')
        tipo_voto = request.json.get('tipo_voto')  # 1 para like, -1 para dislike
        
        if not post_id or tipo_voto not in [1, -1]:
            return jsonify({'success': False, 'message': 'Dados inválidos.'})
        
        resultado = atualizar_votos(post_id, tipo_voto)
        
        if resultado['success']:
            return jsonify({
                'success': True, 
                'novo_votos': resultado['novo_total_votos']
            })
        else:
            return jsonify({'success': False, 'message': resultado['error']})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'})

@app.route('/postagensacademicas')
def postagens_academicas():
    if 'usuario_id' not in session:
        flash('Faça login para acessar esta página.', 'warning')
        return redirect(url_for('login'))
    
    perfil = obter_perfil(session['usuario_id'])
    return render_template('postagensacademicas.html', user=perfil)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/debug_posts')
def debug_posts():
    """Rota para debug - verificar posts e estrutura"""
    posts = obter_posts()
    
    conn = sqlite3.connect('posts.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(posts)")
    posts_structure = cursor.fetchall()
    conn.close()
    
    conn_perfil = sqlite3.connect('perfil.db')
    cursor_perfil = conn_perfil.cursor()
    cursor_perfil.execute("PRAGMA table_info(perfis)")
    perfis_structure = cursor_perfil.fetchall()
    cursor_perfil.execute("SELECT usuario_id, username FROM perfis LIMIT 5")
    perfis_sample = cursor_perfil.fetchall()
    conn_perfil.close()
    
    return jsonify({
        'total_posts': len(posts),
        'posts_structure': posts_structure,
        'perfis_structure': perfis_structure,
        'perfis_sample': perfis_sample,
        'posts': posts[:3]
    })

@app.route('/static/style/perfil/<path:filename>')
def perfil_static(filename):
    return send_from_directory('static/style/perfil', filename)


# app.py - Adicionar estas funções antes da rota /verpostagem

def obter_comentarios(post_id):
    """Obtém todos os comentários de uma postagem específica"""
    try:
        conn = sqlite3.connect('posts.db')
        cursor = conn.cursor()
        
        # Buscar comentários com informações do usuário
        cursor.execute('''
            SELECT c.id, c.post_id, c.usuario_id, c.texto, c.data_criacao, p.username 
            FROM comentarios c 
            LEFT JOIN perfis p ON c.usuario_id = p.usuario_id 
            WHERE c.post_id = ? 
            ORDER BY c.data_criacao ASC
        ''', (post_id,))
        
        comentarios_db = cursor.fetchall()
        conn.close()
        
        comentarios_formatados = []
        for comentario in comentarios_db:
            comentarios_formatados.append({
                'id': comentario[0],
                'post_id': comentario[1],
                'usuario_id': comentario[2],
                'texto': comentario[3],
                'data_criacao': formatar_data(comentario[4]),
                'username': comentario[5] if comentario[5] else f"Usuario_{comentario[2]}"
            })
        
        return comentarios_formatados
        
    except sqlite3.Error as e:
        print(f"Erro ao buscar comentários: {e}")
        return []
    
def criar_tabela_comentarios():
    """Cria a tabela de comentários se não existir"""
    try:
        conn = sqlite3.connect('posts.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comentarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                usuario_id INTEGER NOT NULL,
                texto TEXT NOT NULL,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        conn.close()
        print("Tabela de comentários verificada/criada com sucesso!")
        
    except sqlite3.Error as e:
        print(f"Erro ao criar tabela de comentários: {e}")

def adicionar_comentario(post_id, usuario_id, texto):
    """Adiciona um novo comentário ao banco de dados"""
    try:
        conn = sqlite3.connect('posts.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO comentarios (post_id, usuario_id, texto)
            VALUES (?, ?, ?)
        ''', (post_id, usuario_id, texto))
        
        conn.commit()
        comentario_id = cursor.lastrowid
        conn.close()
        
        return comentario_id
        
    except sqlite3.Error as e:
        print(f"Erro ao adicionar comentário: {e}")
        return None

# Rota para ver postagem individual com comentários
@app.route('/verpostagem')
def ver_postagem():
    """Rota para visualizar uma postagem individual com comentários"""
    post_id = request.args.get('id')
    
    if not post_id:
        flash('ID da postagem não fornecido', 'danger')
        return redirect('/pagtcc')
    
    user = None
    if 'usuario_id' in session:
        user = obter_perfil(session['usuario_id'])
    
    try:
        conn = sqlite3.connect('posts.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
        post_db = cursor.fetchone()
        
        if post_db:
            data_formatada = formatar_data(post_db[7])
            
            post = {
                'id': post_db[0],
                'username': post_db[1],
                'titulo': post_db[2],
                'conteudo': post_db[3],
                'categoria': post_db[4],
                'arquivo': post_db[5],
                'tags': post_db[6],
                'data_criacao': data_formatada,
                'votos': post_db[8] if len(post_db) > 8 else 0,
                'autor_username': post_db[1]
            }
            
            # Obter comentários da postagem
            comentarios = obter_comentarios(post_id)
            
            conn.close()
            return render_template('verpostagem.html', post=post, user=user, comentarios=comentarios)
        else:
            conn.close()
            flash('Postagem não encontrada', 'danger')
            return render_template('verpostagem.html', post=None, user=user)
            
    except Exception as e:
        print(f"Erro ao buscar postagem: {e}")
        flash('Erro ao carregar postagem', 'danger')
        return render_template('verpostagem.html', post=None, user=user)

# Rota para adicionar comentário via AJAX
@app.route('/adicionar_comentario', methods=['POST'])
def adicionar_comentario_route():
    """Rota para adicionar comentários via AJAX"""
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'Faça login para comentar.'})
    
    try:
        post_id = request.json.get('post_id')
        texto = request.json.get('texto')
        
        if not post_id or not texto:
            return jsonify({'success': False, 'message': 'Dados incompletos.'})
        
        comentario_id = adicionar_comentario(post_id, session['usuario_id'], texto)
        
        if comentario_id:
            # Buscar o comentário recém-criado com informações do usuário
            comentarios = obter_comentarios(post_id)
            novo_comentario = comentarios[-1] if comentarios else None
            
            return jsonify({
                'success': True, 
                'comentario_id': comentario_id,
                'comentario': novo_comentario
            })
        else:
            return jsonify({'success': False, 'message': 'Erro ao salvar comentário.'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'})

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# Modificar a parte final do código para:
if __name__ == '__main__':
    init_db()
    migrar_dados_antigos()
    atualizar_estrutura_tabela()
    garantir_usernames()
    corrigir_datas_existentes()
    criar_tabela_comentarios()  # Garantir que a tabela de comentários existe
    app.run(host="0.0.0.0", port=8080, debug=True)