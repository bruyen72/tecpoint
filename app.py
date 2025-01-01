from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import email.utils  # NÃO REMOVER
import os
import json
import uuid
import time
from datetime import datetime
from functools import wraps
from email.utils import formataddr
# Adicione esta linha para poder usar formatdate:
from email.utils import formatdate


# Inicialização do Flask
app = Flask(
    __name__,
    static_folder='static',
    static_url_path=''
)

# Configuração do ambiente e diretórios
if 'RENDER' in os.environ:
    UPLOAD_FOLDER = '/tmp/uploads'
    METADATA_FILE = '/tmp/file_metadata.json'
else:
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
    METADATA_FILE = os.path.join(os.getcwd(), 'file_metadata.json')

# Criar diretório de uploads
try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
except OSError as e:
    print(f"Erro ao criar diretório de uploads: {e}")

# Configurações básicas do Flask
app.config.update(
    SECRET_KEY=os.urandom(24),
    UPLOAD_FOLDER=UPLOAD_FOLDER,
    MAX_CONTENT_LENGTH=50 * 1024 * 1024  # 50MB
)

# Funções auxiliares para metadados
def save_file_metadata(filename, filesize):
    metadata = load_metadata()
    metadata[filename] = {
        'upload_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'size': filesize
    }
    
    try:
        with open(METADATA_FILE, 'w') as f:
            json.dump(metadata, f, indent=4)
    except Exception as e:
        print(f"Erro ao salvar metadados: {e}")

def load_metadata():
    try:
        if os.path.exists(METADATA_FILE):
            with open(METADATA_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar metadados: {e}")
    return {}

# Extensões permitidas
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Configurações de Email
SMTP_SERVER = 'smtps.uhserver.com'
SMTP_PORT = 465
SMTP_USERNAME = 'contato.tec@tecpoint.net.br'
SMTP_PASSWORD = 'tecpoint@2024B'

# Inicialização
db = SQLAlchemy(app)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

# Modelos
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(200), nullable=False)
    pdf_path = db.Column(db.String(200))
    category = db.Column(db.String(50))
    specs = db.Column(db.Text)
    image_paths = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

# Função de envio de email otimizada
def send_email_with_retry(subject, text_content, html_content, recipient, is_internal=False, max_retries=3):
    """Função de envio de email com suporte HTML melhorado"""
    try:
        # Criar mensagem com partes alternativas
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = SMTP_USERNAME
        msg['To'] = recipient
        msg['Date'] = email.utils.formatdate(localtime=True)

        # Exibir nome amigável no FROM
        msg['From'] = formataddr(("TecPoint Soluções", SMTP_USERNAME))

        # Adiciona as versões texto e HTML
        part1 = MIMEText(text_content, 'plain', 'utf-8')
        part2 = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(part1)
        msg.attach(part2)

        # Tenta enviar
        for attempt in range(max_retries):
            try:
                with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                    server.ehlo()
                    server.login(SMTP_USERNAME, SMTP_PASSWORD)
                    server.sendmail(SMTP_USERNAME, [recipient], msg.as_string())
                    print(f"Email enviado para {recipient}")
                    return True
            except Exception as e:
                print(f"Tentativa {attempt + 1} falhou: {e}")
                if attempt == max_retries - 1:
                    return False
                time.sleep(2)
        return False
    except Exception as e:
        print(f"Erro ao enviar email: {e}")
        return False

# Funções auxiliares
def ensure_upload_dir():
    """Garante que o diretório de uploads existe"""
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
        if app.debug:
            os.chmod(app.config['UPLOAD_FOLDER'], 0o777)

def allowed_file(filename):
    """Verifica se a extensão do arquivo é permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file):
    """Salva o arquivo com nome único"""
    if not file or not file.filename:
        return None
    if not allowed_file(file.filename):
        return None
    try:
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        if app.debug:
            os.chmod(file_path, 0o666)
        return unique_filename
    except Exception as e:
        print(f"Erro ao salvar arquivo: {e}")
        return None

def delete_file(filename):
    """Remove um arquivo de forma segura"""
    if filename:
        try:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Erro ao remover arquivo: {e}")

def admin_required(f):
    """Decorador para rotas que requerem autenticação"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.template_filter('json_loads')
def json_loads_filter(json_string):
    """Filtro para carregar JSON de forma segura"""
    try:
        return json.loads(json_string) if json_string else []
    except:
        return []

# Rotas básicas
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/solucoes')
def solucoes():
    return render_template('solucoes.html')

@app.route('/contato')
def contato():
    return render_template('contato.html')

@app.route('/produtos')
def produtos():
    category = request.args.get('category', 'all')
    if category == 'all':
        products = Product.query.order_by(Product.created_at.desc()).all()
    else:
        products = Product.query.filter_by(category=category).order_by(Product.created_at.desc()).all()
    return render_template('produtos.html', products=products, current_category=category)

@app.route('/produto/<int:id>')
def produto_detalhe(id):
    product = Product.query.get_or_404(id)
    related_products = Product.query.filter(
        Product.category == product.category,
        Product.id != product.id
    ).limit(3).all()
    return render_template('produto_detalhe.html', product=product, related_products=related_products)

@app.route('/enviar-cotacao', methods=['POST'])
def enviar_cotacao():
    try:
        dados = {
            'nome': request.form.get('name', '').strip(),
            'email': request.form.get('email', '').strip(),
            'telefone': request.form.get('phone', '').strip(),
            'produto': request.form.get('product_name', '').strip(),
            'categoria': request.form.get('product_category', '').strip(),
            'quantidade': request.form.get('quantity', '1').strip(),
            'mensagem': request.form.get('message', '').strip(),
            'data': datetime.now().strftime('%d/%m/%Y às %H:%M')
        }

        # Mensagem para a TecPoint
        msg_empresa = MIMEMultipart('related')
        msg_empresa['Subject'] = f'Nova Cotação - {dados["produto"]}'
        msg_empresa['From'] = formataddr(("TecPoint Soluções", SMTP_USERNAME))
        msg_empresa['To'] = SMTP_USERNAME
        msg_empresa.add_header('Reply-To', dados['email'])

        html_empresa = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #00A859;">Nova Solicitação de Cotação</h2>
            <div style="margin: 20px 0;">
                <h3>Dados do Cliente</h3>
                <p>
                <strong>Nome:</strong> {dados['nome']}<br>
                <strong>Email:</strong> {dados['email']}<br>
                <strong>Telefone:</strong> {dados['telefone']}</p>
            </div>
            <div style="margin: 20px 0;">
                <h3>Produto Solicitado</h3>
                <p>
                <strong>Produto:</strong> {dados['produto']}<br>
                <strong>Categoria:</strong> {dados['categoria']}<br>
                <strong>Quantidade:</strong> {dados['quantidade']}</p>
            </div>
            <div style="margin: 20px 0;">
                <h3>Mensagem</h3>
                <p>{dados['mensagem']}</p>
            </div>
            <p style="color: #666; font-style: italic;">Recebido em {dados['data']}</p>
        </body>
        </html>
        """
        msg_empresa.attach(MIMEText(html_empresa, 'html', 'utf-8'))

        # Enviar usando SSL/TLS
        with smtplib.SMTP_SSL('smtps.uhserver.com', 465) as server:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg_empresa)

        return jsonify({'message': 'Cotação enviada com sucesso!'}), 200

    except Exception as e:
        print(f'Erro ao enviar cotação: {e}')
        return jsonify({'error': 'Ocorreu um erro inesperado'}), 500

def is_valid_email(email):
    """Valida formato básico do email"""
    try:
        user_part, domain_part = email.rsplit('@', 1)
        return len(user_part) > 0 and len(domain_part) > 3 and '.' in domain_part
    except:
        return False

def save_failed_email(dados):
    """Salva emails que falharam para retry posterior"""
    try:
        with open('failed_emails.json', 'a') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'dados': dados
            }, f)
            f.write('\n')
    except Exception as e:
        print(f"Erro ao salvar email falho: {e}")
@app.route('/enviar-contato-site', methods=['POST'])
def enviar_contato_site():
    try:
        # Validar dados recebidos
        dados = {
            'nome': request.form.get('name', '').strip(),
            'email': request.form.get('email', '').strip(),
            'telefone': request.form.get('phone', '').strip(),
            'mensagem': request.form.get('message', '').strip(),
        }
        
        # Validar campos obrigatórios
        campos_vazios = [k for k, v in dados.items() if not v and k != 'telefone']
        if campos_vazios:
            return jsonify({
                'error': f'Campos obrigatórios não preenchidos: {", ".join(campos_vazios)}'
            }), 400

        # Email em texto plano
        texto_email = f"""
NOVA MENSAGEM DO SITE:

Nome: {dados['nome']}
Email: {dados['email']}
Telefone: {dados['telefone']}

Mensagem:
{dados['mensagem']}

--
Enviado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}
"""

        # Criar mensagem
        msg = MIMEText(texto_email, 'plain', 'utf-8')
        msg['Subject'] = 'Nova Mensagem - Site TecPoint'
        msg['From'] = formataddr(("TecPoint Contato", SMTP_USERNAME))
        msg['To'] = SMTP_USERNAME
        msg.add_header('Reply-To', dados['email'])

        # Enviar email
        try:
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                server.ehlo()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)
                
            return jsonify({'message': 'Mensagem enviada com sucesso!'}), 200
            
        except smtplib.SMTPException as e:
            print(f'Erro SMTP: {e}')
            # Salvar email para tentar reenviar depois
            save_failed_email(dados)
            return jsonify({
                'error': 'Erro ao enviar email. Tente novamente mais tarde.'
            }), 500

    except Exception as e:
        print(f'Erro ao processar contato: {e}')
        return jsonify({'error': 'Erro interno do servidor'}), 500
@app.route('/admin')
@admin_required
def admin_dashboard():
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template('admin/dashboard.html', products=products)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password_hash, password):
            session['admin_logged_in'] = True
            flash('Login realizado com sucesso!')
            return redirect(url_for('admin_dashboard'))
        
        flash('Usuário ou senha incorretos')
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Logout realizado com sucesso!')
    return redirect(url_for('admin_login'))

@app.route('/admin/produtos/adicionar', methods=['GET', 'POST'])
@admin_required
def admin_add_product():
    if request.method == 'POST':
        try:
            # Dados do formulário
            form_data = {
                'name': request.form.get('name'),
                'description': request.form.get('description'),
                'category': request.form.get('category'),
                'specs': request.form.getlist('spec'),
                'image': request.files.get('image'),
                'pdf': request.files.get('pdf'),
                'additional_files': request.files.getlist('images')
            }
            # Validações
            if not all([form_data['name'], form_data['description'], 
                       form_data['category'], form_data['image']]):
                flash('Preencha todos os campos obrigatórios')
                return redirect(url_for('admin_add_product'))

            # Processa especificações
            specs = [s.strip() for s in form_data['specs'] if s.strip()]
            if not specs:
                flash('Adicione pelo menos uma especificação')
                return redirect(url_for('admin_add_product'))

            # Salva imagem principal
            image_filename = save_file(form_data['image'])
            if not image_filename:
                flash('Erro ao salvar imagem principal')
                return redirect(url_for('admin_add_product'))

            # Salva PDF se existir
            pdf_filename = save_file(form_data['pdf']) if form_data['pdf'] else None

            # Processa imagens adicionais
            additional_images = []
            for f in form_data['additional_files']:
                if f:
                    img_name = save_file(f)
                    if img_name:
                        additional_images.append(img_name)

            # Cria produto
            product = Product(
                name=form_data['name'],
                description=form_data['description'],
                category=form_data['category'],
                specs=json.dumps(specs),
                image_path=image_filename,
                pdf_path=pdf_filename,
                image_paths=json.dumps(additional_images) if additional_images else None
            )

            db.session.add(product)
            db.session.commit()
            flash('Produto adicionado com sucesso!')
            return redirect(url_for('admin_dashboard'))

        except Exception as e:
            db.session.rollback()
            print(f"Erro ao adicionar produto: {e}")
            flash('Erro ao adicionar produto')
            return redirect(url_for('admin_add_product'))

    return render_template('admin/add_product.html')

@app.route('/admin/produtos/excluir/<int:id>', methods=['POST'])
@admin_required
def admin_delete_product(id):
    product = Product.query.get_or_404(id)
    
    try:
        # Remove arquivos
        if product.image_path:
            delete_file(product.image_path)
            
        if product.pdf_path:
            delete_file(product.pdf_path)

        if product.image_paths:
            try:
                extra_images = json.loads(product.image_paths)
                for img_file in extra_images:
                    delete_file(img_file)
            except json.JSONDecodeError as e:
                print(f"Erro ao decodificar image_paths: {e}")
        
        db.session.delete(product)
        db.session.commit()
        flash('Produto excluído com sucesso!')

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao excluir produto: {e}")
        flash('Erro ao excluir produto')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve arquivos de upload de forma segura"""
    try:
        if not secure_filename(filename) == filename:
            print(f"Tentativa de acesso a arquivo inseguro: {filename}")
            return "Acesso negado", 403
            
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            print(f"Arquivo não encontrado: {filename}")
            return "Arquivo não encontrado", 404
            
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        print(f"Erro ao servir arquivo {filename}: {e}")
        return "Erro ao acessar arquivo", 500

# Tratamento de erros
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.errorhandler(413)
def request_entity_too_large(e):
    flash('O arquivo enviado é muito grande. Por favor, reduza o tamanho.')
    return redirect(url_for('admin_add_product'))

# Configurações de segurança adicionais
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

# ------------------------------------------------------------------------
# NOVA ROTA /enviar-contato IDENTICA AO /enviar-contato-site:
# (Usando request.get_json(), corpo 'plain', e sem remover nenhum código.)
# -----------------------------------------------------------------------

# Logo após as definições de Product e Admin
@app.before_first_request
def init_database():
    with app.app_context():
        try:
            # Criar todas as tabelas
            db.create_all()
            print("Tabelas criadas com sucesso!")

            # Verificar e criar admin padrão se não existir
            admin = Admin.query.filter_by(username='admin').first()
            if not admin:
                admin = Admin(
                    username='admin',
                    password_hash=generate_password_hash('admin123')
                )
                db.session.add(admin)
                db.session.commit()
                print("Admin criado com sucesso!")

            # Verificar se existem produtos
            produtos_count = Product.query.count()
            print(f"Total de produtos no banco: {produtos_count}")

            # Garantir que a pasta de uploads existe
            uploads_dir = os.path.join(os.getcwd(), 'static', 'uploads')
            if not os.path.exists(uploads_dir):
                os.makedirs(uploads_dir)
                print("Pasta de uploads criada!")

        except Exception as e:
            print(f"Erro na inicialização: {e}")
@app.route('/enviar-contatoTEC', methods=['POST'])
def enviar_contato_form():
    try:
        # Como o formulário está enviando FormData, usamos request.form
        user_name = request.form.get('name', '').strip()
        user_email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        message = request.form.get('message', '').strip()

        # Validação simples
        if not user_name or not user_email or not message:
            return jsonify({'error': 'Todos os campos obrigatórios precisam ser preenchidos'}), 400

        # Criação da mensagem de texto simples
        msg = MIMEText(f"""
NOVA MENSAGEM DO SITE (FormData):

Nome: {user_name}
Email: {user_email}
Telefone: {phone}

Mensagem:
{message}

--
Enviado através do formulário (rota /enviar-contato)
""", 'plain', 'utf-8')
        
        # Ajustando cabeçalhos
        msg['Subject'] = 'Nova Mensagem - Site TecPoint'
        msg['From'] = formataddr(("TecPoint Contato", SMTP_USERNAME))
        msg['To'] = SMTP_USERNAME

        # Adiciona cabeçalho de Reply-To para facilitar respostas ao remetente
        msg.add_header('Reply-To', user_email)

        # Envio do e-mail via SMTP_SSL
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        
        # Retorno de sucesso em JSON
        return jsonify({'message': 'Mensagem enviada com sucesso!'}), 200

    except smtplib.SMTPException as smtp_error:
        print(f'Erro SMTP ao enviar email do site: {smtp_error}')
        return jsonify({'error': 'Erro no envio de e-mail, tente novamente mais tarde'}), 500
    except Exception as e:
        print(f'Erro geral: {e}')
        return jsonify({'error': 'Ocorreu um erro inesperado'}), 500

# ------------------------------------------------------------------------
# FIM NOVA ROTA
# ------------------------------------------------------------------------

if __name__ == '__main__':
    with app.app_context():
        try:
            # Inicializa o banco de dados e garante que todas as tabelas sejam criadas
            print("Inicializando o banco de dados...")
            db.create_all()
            print("Tabelas criadas com sucesso!")

            # Cria admin padrão, caso não exista
            print("Verificando existência do admin padrão...")
            if not Admin.query.filter_by(username='admin').first():
                admin = Admin(
                    username='admin',
                    password_hash=generate_password_hash('admin123')
                )
                db.session.add(admin)
                db.session.commit()
                print("Admin padrão criado com sucesso!")
            else:
                print("Admin padrão já existe.")

            # Configura a porta e inicia o servidor
            port = int(os.environ.get('PORT', 8080))  # Padrão para Fly.io
            print(f"Iniciando o servidor na porta {port}...")
            app.run(host='0.0.0.0', port=port)
        except Exception as e:
            # Tratamento genérico de erro
            print(f"Erro ao inicializar a aplicação: {e}")