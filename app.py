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
import poplib
import email
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger


# Inicialização do Flask
app = Flask(
    __name__,
    static_folder='static',
    static_url_path=''
)

# --------------------------------------------------------------------
# AJUSTE IMPORTANTE PARA USO NO RAILWAY (OU AMBIENTE COM 'DATABASE_URL')
# --------------------------------------------------------------------
# Se 'DATABASE_URL' estiver definido (Railway/Postgres, Heroku etc.),
# use-o; caso contrário, use SQLite local (local.db).
db_uri = os.getenv('DATABASE_URL', 'sqlite:///local.db')

# Correção caso seja 'postgres://' e não 'postgresql://'
# (Heroku, Railway podem gerar 'postgres://' deprecado)
if db_uri.startswith('postgres://'):
    db_uri = db_uri.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

print("=== Usando DB URI:", app.config['SQLALCHEMY_DATABASE_URI'])
# --------------------------------------------------------------------

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
# Extensões permitidas - definir apenas uma vez
ALLOWED_EXTENSIONS = {
    'png', 'jpg', 'jpeg', 'gif',  # imagens
    'pdf', 'doc', 'docx', 'txt'   # documentos
}

def allowed_file(filename):
    """Verifica se a extensão do arquivo é permitida"""
    if not filename:
        return False
    # Verifica extensão
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    return ext in ALLOWED_EXTENSIONS

# Configurações de Email
SMTP_SERVER = 'smtps.uhserver.com'
SMTP_PORT = 465
SMTP_USERNAME = 'contato@tecpoint.net.br'
SMTP_PASSWORD = 'tecpoint@2024B'

# Inicialização
db = SQLAlchemy(app)
# Definir apenas uma vez no início do arquivo
ALLOWED_EXTENSIONS = {
    'png', 'jpg', 'jpeg', 'gif',  # imagens
    'pdf', 'doc', 'docx', 'txt'   # documentos
}
def verificar_emails():
    try:
        # Configurações seguras para o Railway
        server = poplib.POP3_SSL('pop.uhserver.com', 995, timeout=60)
        
        # Login com retry
        try:
            server.user('contato@tecpoint.net.br')
            server.pass_('tecpoint@2024B')
        except Exception as e:
            print(f"Erro de login: {e}")
            return
            
        try:
            # Verifica quantidade de emails
            num_emails = len(server.list()[1])
            
            if num_emails > 0:
                print(f"[{formatdate(localtime=True)}] {num_emails} novo(s) email(s)")
                
                # Processa cada email
                for i in range(num_emails):
                    try:
                        # Obtém o email
                        msg_data = server.retr(i+1)[1]
                        msg = email.message_from_bytes(b'\n'.join(msg_data))
                        
                        # Extrai informações
                        assunto = msg.get('subject', 'Sem assunto')
                        remetente = msg.get('from', 'Desconhecido')
                        
                        print(f"Email {i+1}: De: {remetente} - Assunto: {assunto}")
                        
                    except Exception as e:
                        print(f"Erro ao processar email {i+1}: {e}")
                        continue
                        
            server.quit()
            print("Verificação concluída com sucesso")
            
        except Exception as e:
            print(f"Erro ao verificar emails: {e}")
            server.quit()
            
    except Exception as e:
        print(f"Erro na conexão: {e}")

# Configuração do scheduler com retry
def iniciar_scheduler():
    try:
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            func=verificar_emails,
            trigger=IntervalTrigger(minutes=2),
            id='verificar_emails',
            name='Verificação de Emails',
            replace_existing=True,
            max_instances=1
        )
        scheduler.start()
        print("Verificação automática iniciada")
        return scheduler
    except Exception as e:
        print(f"Erro ao iniciar scheduler: {e}")
        return None

# Inicia com o Flask
@app.before_first_request
def iniciar_verificacao():
    global scheduler
    scheduler = iniciar_scheduler()

# Inicia verificação com o Flask
@app.before_first_request
def iniciar_verificacao():
    scheduler.start()
    print("Verificação automática iniciada")

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
def send_email(subject, html_content, to_email, reply_to=None):
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = formataddr(("TecPoint", SMTP_USERNAME))
        msg['To'] = to_email
        msg['Date'] = formatdate(localtime=True)
        
        if reply_to:
            msg.add_header('Reply-To', reply_to)

        # Gera versão texto do HTML
        text_content = html_content.replace('<br>', '\n').replace('</p>', '\n')
        
        msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))

        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
            server.ehlo()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
            return True
            
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
    """Salva arquivo com validações de segurança"""
    if not file or not file.filename:
        return None
        
    try:
        # Validações básicas
        if not allowed_file(file.filename):
            return None
            
        # Gera nome único e seguro
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Salva arquivo
        file.save(file_path)
        
        # Ajusta permissões em ambiente de desenvolvimento
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

@app.route('/servicos')
def servicos():
    try:
        # Busca serviços ordenados por data de criação
        services = Service.query.order_by(Service.created_at.desc()).all()
        return render_template('servicos.html', services=services)
    except Exception as e:
        print(f"Erro ao buscar serviços: {e}")
        flash('Erro ao carregar serviços')
        return redirect(url_for('index'))

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
            <h2 style="color: #00A859;">Nova Solicitação de Orçamento</h2>
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

        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
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
class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    features = db.Column(db.Text)  # Armazena JSON string de features
    image_path = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property 
    def features_list(self):
        """Retorna features como lista Python"""
        try:
            return json.loads(self.features) if self.features else []
        except json.JSONDecodeError:
            return []
def clean_filename(filename):
    """Sanitize filename and ensure uniqueness"""
    base = secure_filename(filename)
    name, ext = os.path.splitext(base)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{name}_{timestamp}{ext}"

def validate_image(file):
    """Validação completa de imagem"""
    if not file:
        return False
    try:
        # Verifica extensão
        if not allowed_file(file.filename):
            return False
            
        # Verifica tamanho
        file.seek(0, 2)  # Vai para o final do arquivo
        size = file.tell()  # Pega o tamanho
        file.seek(0)  # Volta para o início
        
        if size > app.config['MAX_CONTENT_LENGTH']:
            return False
            
        # Aqui você poderia adicionar mais validações de imagem
        # como verificar dimensões, formato real do arquivo, etc.
        
        return True
    except Exception as e:
        print(f"Erro ao validar imagem: {e}")
        return False
@app.route('/admin')
@admin_required
def admin_dashboard():
    products = Product.query.order_by(Product.created_at.desc()).all()
    services = Service.query.order_by(Service.created_at.desc()).all()
    return render_template('admin/dashboard.html', products=products, services=services)

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
@app.route('/admin/produtos/<int:id>', methods=['GET'])
@admin_required
def get_product(id):
    try:
        product = Product.query.get_or_404(id)
        return jsonify({
            'name': product.name,
            'description': product.description,
            'category': product.category,
            'specs': json.loads(product.specs) if product.specs else []
        })
    except Exception as e:
        print(f"Erro ao buscar produto: {e}")
        return jsonify({'error': 'Erro ao buscar produto'}), 500

@app.route('/admin/produtos/editar/<int:id>', methods=['POST'])
@admin_required
def admin_edit_product(id):
    product = Product.query.get_or_404(id)
    try:
        # Validate required fields
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '').strip()
        specs = request.form.getlist('specs[]')

        if not all([name, description, category]):
            flash('Preencha todos os campos obrigatórios')
            return redirect(url_for('admin_dashboard'))

        # Clean specs list
        specs = [s.strip() for s in specs if s.strip()]

        # Update product data
        product.name = name
        product.description = description
        product.category = category
        product.specs = json.dumps(specs) if specs else None

        # Handle image update if provided
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                # Delete old image
                if product.image_path:
                    delete_file(product.image_path)
                # Save new image
                new_image = save_file(file)
                if new_image:
                    product.image_path = new_image

        # Handle PDF update if provided
        if 'pdf' in request.files:
            pdf_file = request.files['pdf']
            if pdf_file and allowed_file(pdf_file.filename):
                # Delete old PDF
                if product.pdf_path:
                    delete_file(product.pdf_path)
                # Save new PDF
                new_pdf = save_file(pdf_file)
                if new_pdf:
                    product.pdf_path = new_pdf

        # Handle additional images
        if 'images' in request.files:
            additional_files = request.files.getlist('images')
            new_images = []
            old_images = json.loads(product.image_paths) if product.image_paths else []
            
            # Save new images
            for file in additional_files:
                if file and allowed_file(file.filename):
                    img_name = save_file(file)
                    if img_name:
                        new_images.append(img_name)
            
            # Update image paths with both old and new images
            if new_images:
                product.image_paths = json.dumps(old_images + new_images)

        db.session.commit()
        flash('Produto atualizado com sucesso!')

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao atualizar produto: {e}")
        flash('Erro ao atualizar produto')

    return redirect(url_for('admin_dashboard'))
@app.route('/admin/produtos/adicionar', methods=['GET', 'POST'])
@admin_required
def admin_add_product():
    if request.method == 'POST':
        try:
            form_data = {
                'name': request.form.get('name'),
                'description': request.form.get('description'),
                'category': request.form.get('category'),
                'specs': request.form.getlist('spec'),
                'image': request.files.get('image'),
                'pdf': request.files.get('pdf'),
                'additional_files': request.files.getlist('images')
            }
            if not all([form_data['name'], form_data['description'], 
                       form_data['category'], form_data['image']]):
                flash('Preencha todos os campos obrigatórios')
                return redirect(url_for('admin_add_product'))

            specs = [s.strip() for s in form_data['specs'] if s.strip()]
            if not specs:
                flash('Adicione pelo menos uma especificação')
                return redirect(url_for('admin_add_product'))

            image_filename = save_file(form_data['image'])
            if not image_filename:
                flash('Erro ao salvar imagem principal')
                return redirect(url_for('admin_add_product'))

            pdf_filename = save_file(form_data['pdf']) if form_data['pdf'] else None

            additional_images = []
            for f in form_data['additional_files']:
                if f:
                    img_name = save_file(f)
                    if img_name:
                        additional_images.append(img_name)

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

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

# ------------------------------------------------------------------------
@app.route('/enviar-contato-site', methods=['POST'])
def enviar_contato_site():
    try:
        dados = {
            'nome': request.form.get('name', '').strip(),
            'email': request.form.get('email', '').strip(),
            'telefone': request.form.get('phone', '').strip(),
            'mensagem': request.form.get('message', '').strip(),
            'data': datetime.now().strftime('%d/%m/%Y às %H:%M')
        }

        html_content = f"""
        <html><body>
            <h2>Formulário de Contato Recebido - TecPoint</h2>
            <p><strong>Nome:</strong> {dados['nome']}</p>
            <p><strong>Email:</strong> {dados['email']}</p>
            <p><strong>Telefone:</strong> {dados['telefone'] or 'Não informado'}</p>
            <p><strong>Mensagem:</strong><br>{dados['mensagem']}</p>
            <p><em>Recebido em {dados['data']}</em></p>
        </body></html>
        """

        if send_email('Nova Mensagem - Site TecPoint', html_content, SMTP_USERNAME, dados['email']):
            return jsonify({'message': 'Mensagem enviada com sucesso!'}), 200
        else:
            return jsonify({'error': 'Erro ao enviar mensagem'}), 500

    except Exception as e:
        print(f'Erro: {e}')
        return jsonify({'error': 'Erro ao enviar mensagem'}), 500
# -----------------------------------------------------------------------
def add_features_column():
    with app.app_context():
        try:
            db.engine.execute('ALTER TABLE service ADD COLUMN features TEXT')
            print("Coluna 'features' adicionada com sucesso!")
        except Exception as e:
            print(f"Erro ao adicionar coluna: {e}")
            # No app.py, adicione esta função:
def recreate_tables():
    with app.app_context():
        # Remove as tabelas existentes
        db.drop_all()
        
        # Recria todas as tabelas
        db.create_all()
        
        # Recria o admin padrão
        admin = Admin.query.filter_by(username='admin').first()
        if not admin:
            admin = Admin(
                username='admin',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin recriado com sucesso!")

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
            else:
                print("Admin padrão já existe.")

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
        dados = {
            'nome': request.form.get('name', '').strip(),
            'email': request.form.get('email', '').strip(),
            'telefone': request.form.get('phone', '').strip(),
            'mensagem': request.form.get('message', '').strip(),
            'data': datetime.now().strftime('%d/%m/%Y às %H:%M')
        }

        html_content = f"""
        <html><body>
            <h2>Formulário de Contato Recebido - TecPoint</h2>
            <p><strong>Nome:</strong> {dados['nome']}</p>
            <p><strong>Email:</strong> {dados['email']}</p>
            <p><strong>Telefone:</strong> {dados['telefone'] or 'Não informado'}</p>
            <p><strong>Mensagem:</strong><br>{dados['mensagem']}</p>
            <p><em>Recebido em {dados['data']}</em></p>
        </body></html>
        """

        if send_email('Nova Mensagem TEC - Site TecPoint', html_content, SMTP_USERNAME, dados['email']):
            return jsonify({'message': 'Mensagem enviada com sucesso!'}), 200
        else:
            return jsonify({'error': 'Erro ao enviar mensagem'}), 500

    except Exception as e:
        print(f'Erro detalhado: {e}')
        return jsonify({'error': 'Erro ao enviar mensagem'}), 500
#SERVICOS
# ------------------------------------------------------------------------
@app.route('/admin/servicos/adicionar', methods=['GET', 'POST'])
@admin_required
def admin_add_service():
    if request.method == 'POST':
        try:
            # Validate required fields
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            category = request.form.get('category', '').strip()
            features = request.form.getlist('features[]')
            image = request.files.get('image')

            if not all([name, description, category]):
                flash('Preencha todos os campos obrigatórios')
                return redirect(url_for('admin_add_service'))

            if not image or not allowed_file(image.filename):
                flash('Por favor, envie uma imagem válida')
                return redirect(url_for('admin_add_service'))

            # Clean features list
            features = [f.strip() for f in features if f.strip()]
            if not features:
                flash('Adicione pelo menos uma característica')
                return redirect(url_for('admin_add_service'))

            # Save image
            image_filename = save_file(image)
            if not image_filename:
                flash('Erro ao salvar imagem')
                return redirect(url_for('admin_add_service'))

            # Create service
            service = Service(
                name=name,
                description=description,
                category=category,
                features=json.dumps(features),
                image_path=image_filename
            )
            db.session.add(service)
            db.session.commit()
            flash('Serviço adicionado com sucesso!')
            return redirect(url_for('admin_dashboard'))

        except Exception as e:
            db.session.rollback()
            print(f"Erro ao adicionar serviço: {e}")
            flash('Erro ao adicionar serviço')
            return redirect(url_for('admin_add_service'))

    return render_template('admin/add_service.html')

@app.route('/admin/servicos/<int:id>', methods=['GET'])
@admin_required
def get_service(id):
    try:
        service = Service.query.get_or_404(id)
        return jsonify({
            'name': service.name,
            'description': service.description,
            'category': service.category,
            'features': service.features  # Retornar o JSON string original
        })
    except Exception as e:
        print(f"Erro ao buscar serviço: {e}")
        return jsonify({'error': 'Erro ao buscar serviço'}), 500        

@app.route('/admin/servicos/editar/<int:id>', methods=['POST'])
@admin_required
def admin_edit_service(id):
    service = Service.query.get_or_404(id)
    try:
        # Validação de campos
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '').strip()
        features = request.form.getlist('features[]')

        if not all([name, description, category]):
            flash('Preencha todos os campos obrigatórios')
            return redirect(url_for('admin_dashboard'))

        # Limpa e valida features
        features = [f.strip() for f in features if f.strip()]
        if not features:
            flash('Adicione pelo menos uma característica')
            return redirect(url_for('admin_dashboard'))

        # Trata imagem se fornecida
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                if not validate_image(file):
                    flash('Imagem inválida ou muito grande')
                    return redirect(url_for('admin_dashboard'))
                
                try:
                    # Salva nova imagem
                    new_image = save_file(file)
                    if new_image:
                        # Backup da imagem antiga
                        old_image = service.image_path
                        # Atualiza caminho
                        service.image_path = new_image
                        # Remove imagem antiga
                        if old_image:
                            delete_file(old_image)
                    else:
                        flash('Erro ao salvar nova imagem')
                        return redirect(url_for('admin_dashboard'))
                except Exception as e:
                    print(f"Erro ao processar imagem: {e}")
                    flash('Erro ao processar imagem')
                    return redirect(url_for('admin_dashboard'))

        # Atualiza dados do serviço
        service.name = name
        service.description = description
        service.category = category
        service.features = json.dumps(features)

        db.session.commit()
        flash('Serviço atualizado com sucesso!')

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao atualizar serviço: {e}")
        flash('Erro ao atualizar serviço')

    return redirect(url_for('admin_dashboard'))
@app.route('/admin/servicos/excluir/<int:id>', methods=['POST'])
@admin_required
def admin_delete_service(id):
    service = Service.query.get_or_404(id)
    try:
        # Delete associated image file
        if service.image_path:
            delete_file(service.image_path)
        
        db.session.delete(service)
        db.session.commit()
        flash('Serviço excluído com sucesso!')
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao excluir serviço: {e}")
        flash('Erro ao excluir serviço')
    
    return redirect(url_for('admin_dashboard'))

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
            port = int(os.environ.get('PORT', 8080))  # Padrão para Fly.io ou Railway
            print(f"Iniciando o servidor na porta {port}...")
            app.run(host='0.0.0.0', port=port)
        except Exception as e:
            # Tratamento genérico de erro
            print(f"Erro ao inicializar a aplicação: {e}")