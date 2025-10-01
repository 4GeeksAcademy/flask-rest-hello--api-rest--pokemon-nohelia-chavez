import os
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from models import db, User, Region, Pokemon, Favorite



# --- Vistas ---

class UserAdmin(ModelView):
    column_list = ["id", "email", "username", "is_active", "created_at"]
    column_exclude_list = ["password"]
    form_columns = ["email", "password", "username", "is_active"]


class RegionAdmin(ModelView):
    column_list  = ["id", "name", "description", "created_at"]
    form_columns = ["name", "description"]


class PokemonAdmin(ModelView):
    column_list  = [
        "id", "name", "home_region", "sprite_url",
        "base_experience", "height_m", "weight_kg", "created_at"
    ]
    form_columns = ["name", "home_region", "sprite_url", "base_experience", "height_m", "weight_kg"]
    column_labels = {"home_region": "Region"}


class FavoriteAdmin(ModelView):
    column_list  = ["id", "user", "pokemon", "region", "created_at"]
    form_columns = ["user", "pokemon", "region"]

    def on_model_change(self, form, model, is_created):
        """
        Permite guardar si hay al menos UNO:
          - pokemon  (pokemon_id no nulo), o
          - region   (region_id no nulo),
        y también permite ambos. Solo bloquea si los dos están vacíos.
        """
        # Lo que haya ya en el modelo por si SQLAlchemy ya copio los ids
        has_pokemon_model = getattr(model, "pokemon_id", None) is not None
        has_region_model  = getattr(model, "region_id",  None) is not None

        # Lo que viene del formulario por si no se  asignaron los ids 
        has_pokemon_form = bool(getattr(form, "pokemon", None) and form.pokemon.data)
        has_region_form  = bool(getattr(form, "region",  None) and form.region.data)
        # las unimos ambas 
        has_pokemon = has_pokemon_model or has_pokemon_form
        has_region  = has_region_model  or has_region_form
            # valida al menos uno
        if not (has_pokemon or has_region):
            raise ValueError("Selecciona al menos un Pokemi o una region.")

# Setup

def setup_admin(app):
    app.secret_key = os.environ.get('FLASK_APP_KEY', 'sample key')
    app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
    admin = Admin(app, name='Pokémon Admin', template_mode='bootstrap3')

    admin.add_view(UserAdmin(User, db.session))
    admin.add_view(RegionAdmin(Region, db.session))
    admin.add_view(PokemonAdmin(Pokemon, db.session))
    admin.add_view(FavoriteAdmin(Favorite, db.session))