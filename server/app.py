from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response, jsonify
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)

class Restaurants(Resource):
    def get(self):
        restaurants = [restaurant.to_dict(only=('id', 'name', 'address')) for restaurant in Restaurant.query.all()]
        return make_response(jsonify(restaurants), 200)

api.add_resource(Restaurants, "/restaurants")

class RestaurantByID(Resource):
    def get(self, id):
        restaurant = Restaurant.query.filter_by(id=id).first()
        if restaurant is None:
            return make_response(jsonify({"error": "Restaurant not found"}), 404)
        
        response_dict = restaurant.to_dict()
        response_dict['restaurant_pizzas'] = [
            {
                'id': rp.id,
                'price': rp.price,
                'pizza_id': rp.pizza_id,
                'restaurant_id': rp.restaurant_id,
                'pizza': rp.pizza.to_dict(only=('id', 'name', 'ingredients'))
            }
            for rp in restaurant.pizzas
        ]
        return make_response(jsonify(response_dict), 200)
    
    def delete(self, id):
        restaurant = Restaurant.query.filter_by(id=id).first()
        if restaurant is None:
            return make_response(jsonify({"error": "Restaurant not found"}), 404)

        db.session.delete(restaurant)
        db.session.commit()
        return make_response({}, 204)

api.add_resource(RestaurantByID, "/restaurants/<int:id>")

class Pizzas(Resource):
    def get(self):
        pizzas = [pizza.to_dict(only=('id', 'name', 'ingredients')) for pizza in Pizza.query.all()]
        return make_response(jsonify(pizzas), 200)
    
api.add_resource(Pizzas, "/pizzas")

class RestaurantPizzas(Resource):
    def post(self):
        data = request.get_json()
        try:
            price = int(data.get('price'))
            if price < 1 or price > 30:
                raise ValueError("validation errors")
            
            restaurant_pizza = RestaurantPizza(
                pizza_id=data.get('pizza_id'),
                restaurant_id=data.get('restaurant_id'),
                price=price,
            )
            db.session.add(restaurant_pizza)
            db.session.commit()

            response_dict = restaurant_pizza.to_dict()
            response_dict['pizza'] = restaurant_pizza.pizza.to_dict(only=('id', 'name', 'ingredients'))
            response_dict['restaurant'] = restaurant_pizza.restaurant.to_dict(only=('id', 'name', 'address'))
            return make_response(jsonify(response_dict), 201)
        except ValueError as ve:
            return make_response(jsonify({"errors": [str(ve)]}), 400)
        except Exception as e:
            return make_response(jsonify({"errors": ["validation errors"]}), 400)

api.add_resource(RestaurantPizzas, "/restaurant_pizzas")

if __name__ == "__main__":
    app.run(port=5555, debug=True)