# Game_Guesser

Este juego esta inspirado en el juego "Loldle", un juego basado en adivinar que campeon del juego "League of Legends" se ha generado en ese dia.

En este caso, implementaremos el nuestro basado en los mejores videojuegos de todos estos años(segun metacritic), con un dataset de mas de 4000 juegos.

## Tecnologías Utilizadas

### Pandas

Para la limpieza de nuestro dataset, eliminando los datos vacios y extrayendo la informacion interesante para nuestro proyecto, esto se puede observar en nuestro documento game_info.py.

### Docker

Utilizaremos docker para la creación de contenedores, crearemos una red en la cual  se basará en dos partes

- Dos contenedores a modo de base de datos, una con la informacion del dataset de los videojuegos y otra con la información de registros de usuarios.
- Otro que actue de capa para que no haya conexion directa de parte de los usuarios con nuestra información.
- Uno ultimo que sirve como carga de datos para la base de datos.

### FastApi

Mediante FastApi crearemos todo el backend (logica) de nuestro juego, permitiendonos conectarnos a nuestros contenedores docker, como tambien con nuestro frontend basado en html para mostrar el funcionamiento.

## Modo de uso

- Levantar los contenedores con docker-compose up -d

- Ir a la web http://localhost:8000/

## Cómo jugar?

Tendras que iniciar el juego, e ir colocando intentos aleatorios para intentar descubir que juego se ha generado, cuenta con un autocompletado que permitira ver mejor que juegos puedas seleccionar para intentar adivinar.

Tendrás suficientes pistas para poder adivinarlo, ya que por cada intento si aciertas alguna de las categorias con el juego generado, se te mostrará en verde, o en amarillo, si te acercas.

Habra un boton de ayuda (?), donde nos indicará mejor las reglas del juego. A su vez, implementamos un uso de cookies para almacenar un historial de puntos y partidas jugadas.


## Implementaciones Adicionales

- Uso de webscrapping para actualizar valores desactualizados de "Metacritic" en nuestra dataset de videojuegos.

- Implementación junto a Hugging Face de un consultor de pistas para ayudar al usuario.
