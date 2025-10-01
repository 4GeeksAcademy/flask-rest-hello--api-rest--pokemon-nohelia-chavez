from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Boolean, Text, ForeignKey, DateTime, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import List, Optional  # listas de objetos y campos opcionales que aceptan None
from eralchemy2 import render_er   # Generar diagram.png (diagrama ER)

db = SQLAlchemy() # instancia



# USERS

class User(db.Model):
    __tablename__ = "users"                                   # nombre real de la tabla en BD

    id: Mapped[int] = mapped_column(primary_key=True)         # primary key autoincremental.
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)  # email unico 
    password: Mapped[str] = mapped_column(String(255), nullable=False)                         # guarda hash 
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    def __str__(self) -> str:
        return self.username or self.email  
    __repr__ = __str__ # hace que en el admin se vea username en lugar de User 1, 2...

    # 1-N: un usuario tiene muchos favoritos
    favorites: Mapped[List["Favorite"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def serialize(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat()
        }


# REGION

class Region(db.Model):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    def __str__(self) -> str:     
        return self.name            # aqui igual usamos str para que aparezcaen el admin el nombre de y no region 1, 2...
    __repr__ = __str__

    # 1-N: una region tiene muchos pokemis
    pokemons: Mapped[List["Pokemon"]] = relationship(
        back_populates="home_region",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def serialize(self) -> dict:  
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat()
        }


# POKEMONS

class Pokemon(db.Model):
    __tablename__ = "pokemons"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)

    def __str__(self) -> str:
        return self.name
    __repr__ = __str__

    # opcional si se borra la region queda null no se borra el pokemon
    home_region_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("regions.id", ondelete="SET NULL"), nullable=True, index=True
    )
            # atributos informativos de los pokemons excepto create_at
    sprite_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    base_experience: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    # relacion inversas con region desde el pokemon hasta su region
    home_region: Mapped[Optional["Region"]] = relationship(back_populates="pokemons", uselist=False)

    # 1-N: un pokemon puede estar en muchos favoritos
    favorites: Mapped[List["Favorite"]] = relationship(
        back_populates="pokemon",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def serialize(self) -> dict:    # PAra APi
        return {
            "id": self.id,
            "name": self.name,
            "home_region_id": self.home_region_id,
            "sprite_url": self.sprite_url,
            "base_experience": self.base_experience,
            "height_m": self.height_m,
            "weight_kg": self.weight_kg,
            "created_at": self.created_at.isoformat()
        }



# FAVORITES 

class Favorite(db.Model):
    __tablename__ = "favorites"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)   # si borras el user se borran sus favoritos

    # un favorito puede referir a un Pokemon o a una región, ambas columnas son opcionales
    # Si se borra el Pokemon o la Region, ese favorito cae en CASCADE
    pokemon_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("pokemons.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    region_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("regions.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
        # timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    # relaciones inversas hacia user, pokemon y region
    user: Mapped["User"] = relationship(back_populates="favorites", uselist=False)
    pokemon: Mapped[Optional["Pokemon"]] = relationship(back_populates="favorites", uselist=False)
    region: Mapped[Optional["Region"]] = relationship(uselist=False)

    def serialize(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "pokemon_id": self.pokemon_id,
            "region_id": self.region_id,
            "created_at": self.created_at.isoformat()
        }


#  Diagrama 
def draw_erd(output_path: str = "diagram.png") -> None:
    """
    Ejecuta:  pipenv run diagram  (o)  pipenv run python src/models.py
    """
    render_er(db.Model, output_path)
    print(f"Diagrama generado en {output_path}")


if __name__ == "__main__":
    draw_erd()