from flask import Flask, render_template, request, redirect, url_for, jsonify
import mysql.connector
import pusher

app = Flask(__name__)

# Configuración de Pusher para actualizaciones en tiempo real
pusher_client = pusher.Pusher(
    app_id="1767326",
    key="42b9b4800a5a14fc436c",
    secret="569fb5bfe16d510b6ce7",
    cluster="us2",
)

# Patrón Singleton para la conexión a la base de datos
class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            try:
                cls._instance = mysql.connector.connect(
                    host='localhost',
                    user='root',
                    password='',
                    database='simaec'
                )
            except mysql.connector.Error as err:
                print(f"Error de conexión: {err}")
                raise
        return cls._instance



# Modelo para interactuar con la tabla thresholdslimits
class ThresholdsModel:
    def __init__(self):
        self.db = Database()

    def get_all_thresholds(self):
        cursor = self.db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM thresholdslimits")
        thresholds = cursor.fetchall()
        cursor.close()
        return thresholds

    def add_threshold(self, min_limit, max_limit, min_threshold, max_threshold):
        cursor = self.db.cursor()
        query = """
            INSERT INTO thresholdslimits (minLimit, maxLimit, minThreshold, maxThreshold)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (min_limit, max_limit, min_threshold, max_threshold))
        self.db.commit()
        cursor.close()

    def delete_threshold(self, id_limit):
        cursor = self.db.cursor()
        query = "DELETE FROM thresholdslimits WHERE IDLimThres = %s"
        cursor.execute(query, (id_limit,))
        self.db.commit()
        cursor.close()

# Comandos para insertar y eliminar umbrales
class AddThresholdCommand:
    def __init__(self, model, min_limit, max_limit, min_threshold, max_threshold):
        self.model = model
        self.min_limit = min_limit
        self.max_limit = max_limit
        self.min_threshold = min_threshold
        self.max_threshold = max_threshold

    def execute(self):
        self.model.add_threshold(self.min_limit, self.max_limit, self.min_threshold, self.max_threshold)

class DeleteThresholdCommand:
    def __init__(self, model, id_limit):
        self.model = model
        self.id_limit = id_limit

    def execute(self):
        self.model.delete_threshold(self.id_limit)

# Presentador que maneja la lógica de la vista
class ThresholdsPresenter:
    def __init__(self):
        self.model = ThresholdsModel()

    def get_all_thresholds(self):
        return self.model.get_all_thresholds()

    def add_threshold(self, min_limit, max_limit, min_threshold, max_threshold):
        command = AddThresholdCommand(self.model, min_limit, max_limit, min_threshold, max_threshold)
        command.execute()

    def delete_threshold(self, id_limit):
        command = DeleteThresholdCommand(self.model, id_limit)
        command.execute()


# Clase para manejar las operaciones de usuarios
class UserFacade:
    def __init__(self):
        self.conn = Database()

    def get_all_users(self):
        """Recupera todos los usuarios registrados de la base de datos."""
        cursor = self.conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT IDUser, name, email, user FROM usuarios")
            usuarios = cursor.fetchall()
            return usuarios
        except mysql.connector.Error as err:
            print(f"Error al obtener usuarios: {err}")
            return []
        finally:
            cursor.close()

    def get_user_by_id(self, user_id):
        """Obtiene la información de un usuario por su ID."""
        cursor = self.conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT IDUser, name, email, user FROM usuarios WHERE IDUser = %s", (user_id,))
            usuario = cursor.fetchone()
            return usuario
        except mysql.connector.Error as err:
            print(f"Error al obtener usuario: {err}")
            return None
        finally:
            cursor.close()

    def update_user(self, user_id, name, email, username):
        """Actualiza la información de un usuario en la base de datos."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "UPDATE usuarios SET name = %s, email = %s, user = %s WHERE IDUser = %s",
                (name, email, username, user_id)
            )
            self.conn.commit()

            # Emitir un evento de Pusher para actualización
            pusher_client.trigger('user-channel', 'user-updated', {
                'id': user_id,
                'name': name,
                'email': email,
                'user': username
            })
        except mysql.connector.Error as err:
            print(f"Error al actualizar usuario: {err}")
            self.conn.rollback()
        finally:
            cursor.close()

    def delete_user(self, user_id):
        """Elimina un usuario de la base de datos."""
        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM usuarios WHERE IDUser = %s", (user_id,))
            self.conn.commit()

            # Emitir un evento de Pusher para eliminación
            pusher_client.trigger('user-channel', 'user-deleted', {'id': user_id})
        except mysql.connector.Error as err:
            print(f"Error al eliminar usuario: {err}")
            self.conn.rollback()
        finally:
            cursor.close()


# Clase para manejar las operaciones de usuarios
class UserFacade:
    def __init__(self):
        self.conn = Database()

    def get_all_users(self):
        """Recupera todos los usuarios registrados de la base de datos."""
        cursor = self.conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT IDUser, name, email, user FROM usuarios")
            usuarios = cursor.fetchall()
            return usuarios
        except mysql.connector.Error as err:
            print(f"Error al obtener usuarios: {err}")
            return []
        finally:
            cursor.close()

    def get_user_by_id(self, user_id):
        """Obtiene la información de un usuario por su ID."""
        cursor = self.conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT IDUser, name, email, user FROM usuarios WHERE IDUser = %s", (user_id,))
            usuario = cursor.fetchone()
            return usuario
        except mysql.connector.Error as err:
            print(f"Error al obtener usuario: {err}")
            return None
        finally:
            cursor.close()

    def update_user(self, user_id, name, email, username):
        """Actualiza la información de un usuario en la base de datos."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "UPDATE usuarios SET name = %s, email = %s, user = %s WHERE IDUser = %s",
                (name, email, username, user_id)
            )
            self.conn.commit()
            
            # Emitir un evento de Pusher para actualización
            pusher_client.trigger('user-channel', 'user-updated', {
                'id': user_id,
                'name': name,
                'email': email,
                'user': username
            })
        except mysql.connector.Error as err:
            print(f"Error al actualizar usuario: {err}")
            self.conn.rollback()
        finally:
            cursor.close()

    def delete_user(self, user_id):
        """Elimina un usuario de la base de datos."""
        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM usuarios WHERE IDUser = %s", (user_id,))
            self.conn.commit()
            
            # Emitir un evento de Pusher para eliminación
            pusher_client.trigger('user-channel', 'user-deleted', {'id': user_id})
        except mysql.connector.Error as err:
            print(f"Error al eliminar usuario: {err}")
            self.conn.rollback()
        finally:
            cursor.close()

# Presenter que gestiona la lógica entre la vista y el modelo
class UserPresenter:
    def __init__(self):
        self.user_facade = UserFacade()

    def get_all_users(self):
        """Obtiene todos los usuarios y los pasa a la vista."""
        return self.user_facade.get_all_users()

    def get_user_by_id(self, user_id):
        """Obtiene un usuario específico y lo pasa a la vista."""
        return self.user_facade.get_user_by_id(user_id)

    def add_user(self, name, email, username, password):
        """Agrega un usuario nuevo a la base de datos."""
        conn = Database()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO usuarios (name, email, user, password) VALUES (%s, %s, %s, %s)",
                (name, email, username, password)
            )
            conn.commit()
            
            # Obtener el ID del usuario insertado
            user_id = cursor.lastrowid
            
            # Emitir un evento de Pusher para inserción
            pusher_client.trigger('user-channel', 'user-added', {
                'id': user_id,
                'name': name,
                'email': email,
                'user': username
            })
        except mysql.connector.Error as err:
            print(f"Error de base de datos: {err}")
            conn.rollback()
        finally:
            cursor.close()

    def update_user(self, user_id, name, email, username):
        """Actualiza la información de un usuario."""
        self.user_facade.update_user(user_id, name, email, username)

    def delete_user(self, user_id):
        """Elimina un usuario de la base de datos."""
        self.user_facade.delete_user(user_id)


# Instancia del Presenter
user_presenter = UserPresenter()


@app.route('/')
def start():
    db = Database()
    cursor = db.cursor()

    # Consultar el último registro de temperatura y humedad
    cursor.execute("SELECT temperature, humidity FROM measurements ORDER BY dateTima DESC LIMIT 1")
    data = cursor.fetchone()

    # Si no hay datos en la base de datos, asignamos valores predeterminados
    if data:
        temperature = data[0]
        humidity = data[1]
    else:
        temperature = None
        humidity = None

    # Retornar los datos a la plantilla
    return render_template('start.html', temperature=temperature, humidity=humidity)

@app.route('/trigger-update')
def trigger_update():
    db = Database()
    cursor = db.cursor()

    # Consultar el último registro de temperatura y humedad
    cursor.execute("SELECT temperature, humidity FROM measurements ORDER BY IDmeasurement DESC LIMIT 1")
    data = cursor.fetchone()

    # Emitir los datos más recientes a través de Pusher
    if data:
        pusher_client.trigger('measurements-channel', 'new-measurement', {
            'temperature': data[0],
            'humidity': data[1]
        })

    return jsonify({'status': 'success'})


@app.route('/signup')
def signup():
    return render_template("signup.html")

@app.route('/signup', methods=['POST'])
def register_user():
    try:
        nombre = request.form['txtNombre']
        email = request.form['txtEmailSU']
        usuario = request.form['txtUserSU']
        password = request.form['txtPasswordSU']
    except KeyError as e:
        return f"Missing key: {str(e)}", 400

    user_presenter.add_user(nombre, email, usuario, password)
    return render_template("signup.html", success=True)


# Vista (Ruta para mostrar la temperatura)
@app.route('/temperatures')
def temperatures():
    db = Database()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM thresholdslimits")  # Obtener todos los registros de la base de datos
    thresholds = cursor.fetchall()  # Almacenamos los resultados de la consulta
    cursor.close()  # Cerramos el cursor después de obtener los datos
    return render_template('temperatures.html', thresholds=thresholds)

@app.route('/insert_threshold', methods=['POST'])
def insert_threshold():
    minLimit = request.form['minLimit']
    maxLimit = request.form['maxLimit']
    minThreshold = request.form['minThreshold']
    maxThreshold = request.form['maxThreshold']

    db = Database()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO thresholdslimits (minLimit, maxLimit, minThreshold, maxThreshold)
        VALUES (%s, %s, %s, %s)
    """, (minLimit, maxLimit, minThreshold, maxThreshold))
    db.commit()
    cursor.close()  # Cerramos el cursor después de la inserción

    # Emitir evento a Pusher para notificar a los clientes conectados sobre el nuevo registro
    pusher_client.trigger('threshold-channel', 'new-threshold', {
        'id': cursor.lastrowid,
        'minLimit': minLimit,
        'maxLimit': maxLimit,
        'minThreshold': minThreshold,
        'maxThreshold': maxThreshold
    })

    return jsonify({'success': True})

@app.route('/delete_threshold/<int:id>', methods=['POST'])
def delete_threshold(id):
    db = Database()
    cursor = db.cursor()
    cursor.execute("""
        DELETE FROM thresholdslimits WHERE IDLimThres = %s
    """, (id,))
    db.commit()
    cursor.close()  # Cerramos el cursor después de la eliminación

    # Emitir evento a Pusher para notificar la eliminación
    pusher_client.trigger('threshold-channel', 'delete-threshold', {
        'id': id
    })

    return jsonify({'success': True})

@app.route('/userInfo')
def userInfo():
    """Muestra la información de los usuarios registrados en la base de datos."""
    usuarios = user_presenter.get_all_users()
    return render_template("userInfo.html", users=usuarios)


@app.route('/delete_user', methods=['POST'])
def delete_user():
    data = request.get_json()
    
    if 'user_id' not in data:
        app.logger.error("Falta el parámetro 'user_id'")
        return jsonify({'success': False, 'error': 'Parámetro falta en la solicitud'}), 400

    user_id = data['user_id']
    app.logger.info(f"Eliminando usuario con ID: {user_id}")
    
    try:
        user_presenter.delete_user(user_id)
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error al eliminar usuario: {str(e)}")
        return jsonify({'success': False, 'error': 'No se pudo eliminar el usuario'}), 500


@app.route('/edit_user/<int:user_id>')
def edit_user(user_id):
    """Carga la información de un usuario para editarla."""
    usuario = user_presenter.get_user_by_id(user_id)
    if not usuario:
        return "Usuario no encontrado", 404
    return render_template("modifyInfoUser.html", user=usuario)

@app.route('/edit_user/<int:user_id>', methods=['POST'])
def save_user(user_id):
    """Guarda los cambios realizados a un usuario."""
    try:
        name = request.form['name']
        email = request.form['email']
        username = request.form['user']
    except KeyError as e:
        return f"Missing key: {str(e)}", 400

    user_presenter.update_user(user_id, name, email, username)
    return redirect(url_for('userInfo'))


if __name__ == '__main__':
    app.run(debug=True)
