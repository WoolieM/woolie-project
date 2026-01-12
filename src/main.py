from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel
from enum import Enum

app = FastAPI()


fake_db = {
    1:  {'name': 'woolie', 'age': 14, 'country': 'Australia'},
    2:  {'name': 'Cassy', 'age': 22, 'country': 'UK'}
}


class EmployeeUpdate(BaseModel):
    name: str
    age: int
    country: str


class Item(BaseModel):
    name: str
    price: float
    description: str | None = None
    tax: float | None = None


class UserPublic(BaseModel):
    username: str
    email: str


class Message(BaseModel):
    message: str


class UserLogin(BaseModel):
    username: str
    password: str


@app.post('/login/{my_login}', response_model= UserPublic | Message)
def login(my_login: str, user_data: UserLogin):
    if my_login == 'yes':
        user_from_db = {
            'username': 'woolie',
            'email': 'woo@woo.woo',
            'test1': 'fake',
            'test2': 'fake2'
        }
        return user_from_db
    else:
        return {"message": "you are wrong"}


@app.get("/employee/{emp_id}")
def get_employee(emp_id: int):
    current_employee = fake_db.get(emp_id)
    return current_employee


@app.get("/employee/aa/{emp_id}")
def get_employee_aa(emp_id: int):
    return fake_db.get(emp_id)


@app.put("/employee/{emp_id}")
def update_employee(emp_id: int, employee: EmployeeUpdate):
    if emp_id in fake_db:
        fake_db[emp_id] = employee.model_dump()

        return {"message": "update good", "newdata": fake_db.get(emp_id)}
    else:
        return {"message": "not found"}


@app.get("/items/{item_id}")
async def read_item(
        item_id: str,
        q: str,
        short: bool = False
        
    ):
    item = {'item_id': item_id}
    if q:
        item.update({'q': q})
    if not short:
        item.update(
            {'description': 'This sucks'}
        )
    return item


@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item):
    return {
        'item_id_up': item_id,
        **item.model_dump()
    }


class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


@app.get("/model/{model_name}")
async def get_model(model_name: ModelName):
    if model_name == ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}
    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}
    return {"model_name": model_name, "message": "Have some residuals"}


@app.get("/items_aa/{item_id}")
async def read_user_item(
        item_id: str,
        needy: str,
        skip: int = 0,
        limit: int | None = None
        
    ):
    item = {
        'item_id': item_id,
        'needy': needy,
        'skip': skip,
        'limit': limit
    }
    return item


@app.post('/item/')
async def create_item(item: Item):
    item_dict = item.model_dump()
    if item.tax is not None:
        price_with_tax = item.price + item.tax
    item_dict.update({'price and tax': price_with_tax})
    return item_dict