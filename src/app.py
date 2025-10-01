"""
API Server: Pokémon-style SWAPI
"""
import os
from flask import Flask, request, jsonify
from flask_migrate import Migrate
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Region, Pokemon, Favorite

app = Flask(__name__)
app.url_map.strict_slashes = False

# DB config
db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Errors JSON 
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

#  Sitemap 
@app.route('/')
def sitemap():
    return generate_sitemap(app)


# Helpers
def get_current_user_id() -> int:
    """
    Obtiene el "usuario actual" SIN auth real:
    - Prioriza ?user_id=123 en querystring
    - Luego header X-User-Id: 123
    - Si no hay, intenta usar el primer usuario en BD
    """
    q_id = request.args.get("user_id")
    if q_id and q_id.isdigit():
        return int(q_id)

    h_id = request.headers.get("X-User-Id")
    if h_id and h_id.isdigit():
        return int(h_id)

    first = User.query.order_by(User.id.asc()).first()
    if not first:
        raise APIException("No hay usuarios en la base de datos. Crea uno en el Admin.", 400)
    return first.id

def ensure_user_exists(user_id: int) -> User:
    user = User.query.get(user_id)
    if not user:
        raise APIException(f"User {user_id} no existe.", 404)
    return user


# POKEMONS

@app.route('/pokemons', methods=['GET'])
def list_pokemons():
    pokemons = Pokemon.query.order_by(Pokemon.id.asc()).all()
    return jsonify([p.serialize() for p in pokemons]), 200

@app.route('/pokemons/<int:pokemon_id>', methods=['GET'])
def get_pokemon(pokemon_id):
    p = Pokemon.query.get(pokemon_id)
    if not p:
        raise APIException("Pokémon no encontrado.", 404)
    return jsonify(p.serialize()), 200


# REGIONS

@app.route('/regions', methods=['GET'])
def list_regions():
    regions = Region.query.order_by(Region.id.asc()).all()
    return jsonify([r.serialize() for r in regions]), 200

@app.route('/regions/<int:region_id>', methods=['GET'])
def get_region(region_id):
    r = Region.query.get(region_id)
    if not r:
        raise APIException("Región no encontrada.", 404)
    return jsonify(r.serialize()), 200


# USERS (lista)

@app.route('/users', methods=['GET'])
def list_users():
    users = User.query.order_by(User.id.asc()).all()
    return jsonify([u.serialize() for u in users]), 200


# FAVORITES del usuario actual

@app.route('/users/favorites', methods=['GET'])
def list_my_favorites():
    user_id = get_current_user_id()
    ensure_user_exists(user_id)

    favs = Favorite.query.filter_by(user_id=user_id).order_by(Favorite.id.asc()).all()
    out = []
    for f in favs:
        item = f.serialize()
        # enriquecemos un poco la respuesta
        if f.pokemon_id:
            p = Pokemon.query.get(f.pokemon_id)
            item["pokemon"] = p.serialize() if p else None
        if f.region_id:
            r = Region.query.get(f.region_id)
            item["region"] = r.serialize() if r else None
        out.append(item)
    return jsonify(out), 200


# ADD / DELETE FAVORITES (pokemon / region)

@app.route('/favorite/pokemon/<int:pokemon_id>', methods=['POST'])
def add_fav_pokemon(pokemon_id):
    user_id = get_current_user_id()
    ensure_user_exists(user_id)

    p = Pokemon.query.get(pokemon_id)
    if not p:
        raise APIException("Pokémon no encontrado.", 404)

    # Evita duplicados
    exists = Favorite.query.filter_by(user_id=user_id, pokemon_id=pokemon_id).first()
    if exists:
        return jsonify({"msg": "Ya estaba en favoritos", "favorite": exists.serialize()}), 200

    fav = Favorite(user_id=user_id, pokemon_id=pokemon_id, region_id=None)
    db.session.add(fav)
    db.session.commit()
    return jsonify(fav.serialize()), 201

@app.route('/favorite/region/<int:region_id>', methods=['POST'])
def add_fav_region(region_id):
    user_id = get_current_user_id()
    ensure_user_exists(user_id)

    r = Region.query.get(region_id)
    if not r:
        raise APIException("Región no encontrada.", 404)

    # Evitar duplicados
    exists = Favorite.query.filter_by(user_id=user_id, region_id=region_id).first()
    if exists:
        return jsonify({"msg": "Ya estaba en favoritos", "favorite": exists.serialize()}), 200

    fav = Favorite(user_id=user_id, region_id=region_id, pokemon_id=None)
    db.session.add(fav)
    db.session.commit()
    return jsonify(fav.serialize()), 201

@app.route('/favorite/pokemon/<int:pokemon_id>', methods=['DELETE'])
def delete_fav_pokemon(pokemon_id):
    user_id = get_current_user_id()
    ensure_user_exists(user_id)

    fav = Favorite.query.filter_by(user_id=user_id, pokemon_id=pokemon_id).first()
    if not fav:
        raise APIException("Ese Pokémon no está en tus favoritos.", 404)

    db.session.delete(fav)
    db.session.commit()
    return jsonify({"msg": "Favorito (Pokémon) eliminado"}), 200

@app.route('/favorite/region/<int:region_id>', methods=['DELETE'])
def delete_fav_region(region_id):
    user_id = get_current_user_id()
    ensure_user_exists(user_id)

    fav = Favorite.query.filter_by(user_id=user_id, region_id=region_id).first()
    if not fav:
        raise APIException("Esa Región no está en tus favoritos.", 404)

    db.session.delete(fav)
    db.session.commit()
    return jsonify({"msg": "Favorito (Región) eliminado"}), 200


# Run

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=True)
